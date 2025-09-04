"""
LangChain provider for auto-research system with Azure OpenAI, Search API, and Multi-agent coordination
"""

import os
import json
import asyncio
import concurrent.futures
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from .base import ResearchProvider

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    from tavily import TavilyClient
    TAVILY_AVAILABLE = True
except ImportError:
    TAVILY_AVAILABLE = False

@dataclass
class SubQuery:
    """Sub-query for multi-agent research"""
    query: str
    priority: int
    domain: str
    context: str = ""

@dataclass
class AgentResult:
    """Result from a research agent"""
    agent_id: str
    query: str
    content: str
    sources: List[Dict[str, Any]]
    confidence_score: float
    domain: str

class ResearchSupervisor:
    """Supervisor for multi-agent research coordination"""
    
    def __init__(self, openai_client, logger):
        self.client = openai_client
        self.logger = logger
    
    def decompose_query(self, query: str, context: str) -> List[SubQuery]:
        """Decompose main query into sub-queries for parallel processing"""
        decomposition_prompt = f"""
        あなたは研究戦略の専門家です。以下のメインクエリと文脈を分析し、並列処理可能な3つの専門的なサブクエリに分解してください。

        メインクエリ: {query}
        
        文脈: {context}

        各サブクエリは以下の形式で出力してください：
        1. [ドメイン名] クエリ内容 (優先度: 1-3)
        2. [ドメイン名] クエリ内容 (優先度: 1-3)  
        3. [ドメイン名] クエリ内容 (優先度: 1-3)

        ドメイン例: 技術動向, 市場分析, 学術研究, 実装手法, 将来展望など
        優先度: 1=最重要, 2=重要, 3=補足
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": decomposition_prompt}],
                max_tokens=800,
                temperature=0.3
            )
            
            content = response.choices[0].message.content
            sub_queries = []
            
            # Parse the response to extract sub-queries
            lines = content.strip().split('\n')
            for i, line in enumerate(lines, 1):
                if line.strip() and any(char.isdigit() for char in line[:5]):
                    # Extract domain, query and priority
                    if '[' in line and ']' in line:
                        domain_start = line.find('[') + 1
                        domain_end = line.find(']')
                        domain = line[domain_start:domain_end]
                        
                        query_part = line[domain_end+1:].strip()
                        
                        # Extract priority
                        priority = 2  # default
                        if '優先度:' in query_part or 'priority:' in query_part.lower():
                            if '1' in query_part[-10:]:
                                priority = 1
                            elif '3' in query_part[-10:]:
                                priority = 3
                            query_part = query_part.split('(優先度')[0].split('(priority')[0].strip()
                        
                        sub_queries.append(SubQuery(
                            query=query_part,
                            priority=priority,
                            domain=domain,
                            context=context[:500]  # Truncate context
                        ))
            
            if len(sub_queries) < 3:
                # Fallback to default decomposition
                self.logger.warning("Failed to parse sub-queries, using fallback")
                return [
                    SubQuery("技術動向と最新の進展", 1, "技術動向", context[:500]),
                    SubQuery("実用化・実装における課題と解決策", 2, "実装手法", context[:500]),
                    SubQuery("将来の展望と影響分析", 2, "将来展望", context[:500])
                ]
            
            return sub_queries[:3]  # Limit to 3 sub-queries
            
        except Exception as e:
            self.logger.error(f"Error in query decomposition: {e}")
            # Fallback
            return [
                SubQuery("技術動向と最新の進展", 1, "技術動向", context[:500]),
                SubQuery("実用化・実装における課題と解決策", 2, "実装手法", context[:500]),
                SubQuery("将来の展望と影響分析", 2, "将来展望", context[:500])
            ]

class ContextCompressor:
    """Context compression for token optimization"""
    
    def __init__(self, openai_client, logger):
        self.client = openai_client
        self.logger = logger
    
    def compress_context(self, context: str, threshold: int = 4000) -> str:
        """Compress context if it exceeds threshold"""
        if len(context) <= threshold:
            return context
        
        compression_prompt = f"""
        以下の長いコンテンツを{threshold//2}文字程度に要約してください。重要な情報を保持し、研究に必要な文脈を維持してください。

        コンテンツ:
        {context}
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": compression_prompt}],
                max_tokens=1000,
                temperature=0.1
            )
            
            compressed = response.choices[0].message.content
            self.logger.info(f"Context compressed from {len(context)} to {len(compressed)} characters")
            return compressed
            
        except Exception as e:
            self.logger.error(f"Error in context compression: {e}")
            # Fallback to truncation
            return context[:threshold] + "\n\n[...内容が切り詰められました...]"

class ResearchAgent:
    """Individual research agent for specialized queries"""
    
    def __init__(self, agent_id: str, openai_client, search_client, logger):
        self.agent_id = agent_id
        self.openai_client = openai_client
        self.search_client = search_client
        self.logger = logger
    
    def conduct_specialized_research(self, sub_query: SubQuery) -> AgentResult:
        """Conduct specialized research for a sub-query"""
        self.logger.info(f"Agent {self.agent_id} researching: {sub_query.query}")
        
        # Phase 3: Search integration
        search_results = []
        sources = []
        
        if self.search_client and TAVILY_AVAILABLE:
            try:
                search_response = self.search_client.search(
                    query=sub_query.query,
                    search_depth="deep",
                    max_results=5
                )
                search_results = search_response.get('results', [])
                sources = [{'title': r.get('title', ''), 'url': r.get('url', ''), 'content': r.get('content', '')[:500]} 
                          for r in search_results]
            except Exception as e:
                self.logger.warning(f"Search API error: {e}")
        
        # Create specialized research prompt
        search_context = ""
        if search_results:
            search_context = "\n\n参考情報:\n"
            for i, result in enumerate(search_results, 1):
                search_context += f"{i}. {result.get('title', '')}: {result.get('content', '')[:300]}\n"
        
        research_prompt = f"""
        あなたは{sub_query.domain}の専門研究者です。以下の専門的な観点から詳細な分析を行ってください。

        研究クエリ: {sub_query.query}
        
        文脈: {sub_query.context}
        {search_context}

        以下の構造で回答してください：
        ## 現状分析
        ## 重要な発見・トレンド
        ## 実用化への示唆
        ## 今後の展望
        
        専門性を活かした深い洞察と具体的な行動提案を含めてください。
        """
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": research_prompt}],
                max_tokens=2000,
                temperature=0.7
            )
            
            content = response.choices[0].message.content
            
            # Calculate confidence score based on search results and content quality
            confidence_score = 0.7  # Base score
            if search_results:
                confidence_score += 0.2
            if len(content) > 1000:
                confidence_score += 0.1
            
            return AgentResult(
                agent_id=self.agent_id,
                query=sub_query.query,
                content=content,
                sources=sources,
                confidence_score=min(confidence_score, 1.0),
                domain=sub_query.domain
            )
            
        except Exception as e:
            self.logger.error(f"Agent {self.agent_id} research failed: {e}")
            return AgentResult(
                agent_id=self.agent_id,
                query=sub_query.query,
                content=f"研究中にエラーが発生しました: {str(e)}",
                sources=[],
                confidence_score=0.1,
                domain=sub_query.domain
            )

class LangChainProvider(ResearchProvider):
    """LangChain provider with Azure OpenAI, Search API, and Multi-agent coordination"""
    
    def __init__(self, config: Dict[str, Any], logger):
        super().__init__(config, logger)
        
        # Phase 2: Azure OpenAI integration
        self.openai_client = None
        if OPENAI_AVAILABLE:
            self._setup_openai_client()
        
        # Phase 3: Search API integration
        self.search_client = None
        if TAVILY_AVAILABLE:
            self._setup_search_client()
        
        # Phase 4: Multi-agent components
        self.supervisor = None
        self.compressor = None
        if self.openai_client:
            self.supervisor = ResearchSupervisor(self.openai_client, logger)
            self.compressor = ContextCompressor(self.openai_client, logger)
        
        # Configuration
        self.max_sub_agents = int(config.get('MAX_SUB_AGENTS', 3))
        self.context_compression_threshold = int(config.get('CONTEXT_COMPRESSION_THRESHOLD', 4000))
        self.parallel_execution_timeout = int(config.get('PARALLEL_EXECUTION_TIMEOUT', 300))
    
    def _setup_openai_client(self):
        """Setup Azure OpenAI client"""
        try:
            api_key = self.config.get('AZURE_OPENAI_API_KEY')
            base_url = self.config.get('AZURE_OPENAI_BASE_URL')
            
            if not api_key or not base_url:
                self.logger.error("Azure OpenAI configuration missing")
                return
            
            self.openai_client = OpenAI(
                api_key=api_key,
                base_url=base_url
            )
            self.logger.info("Azure OpenAI client initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to setup OpenAI client: {e}")
    
    def _setup_search_client(self):
        """Setup Tavily search client"""
        try:
            api_key = self.config.get('TAVILY_API_KEY')
            if not api_key:
                self.logger.warning("TAVILY_API_KEY not found, search functionality disabled")
                return
            
            self.search_client = TavilyClient(api_key=api_key)
            self.logger.info("Tavily search client initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to setup search client: {e}")
    
    def get_provider_name(self) -> str:
        return "langchain"
    
    def validate_config(self) -> bool:
        """Validate LangChain provider configuration"""
        required_keys = ['AZURE_OPENAI_API_KEY', 'AZURE_OPENAI_BASE_URL']
        
        for key in required_keys:
            if not self.config.get(key):
                self.logger.error(f"Required configuration {key} not found")
                return False
        
        if not OPENAI_AVAILABLE:
            self.logger.error("OpenAI library not available. Install with: pip install openai")
            return False
        
        return True
    
    def conduct_research(self, prompt: str) -> Optional[Dict[str, Any]]:
        """
        Conduct research using LangChain provider with multi-agent coordination
        
        Args:
            prompt: The research prompt
            
        Returns:
            Dictionary containing research results or None if failed
        """
        if not self.validate_config() or not self.openai_client:
            return None
        
        try:
            self.logger.info("Starting LangChain multi-agent research...")
            
            # Phase 4: Context compression if needed
            if self.compressor and len(prompt) > self.context_compression_threshold:
                prompt = self.compressor.compress_context(prompt, self.context_compression_threshold)
            
            # Phase 4: Query decomposition
            if self.supervisor:
                sub_queries = self.supervisor.decompose_query(prompt, prompt[:1000])
            else:
                # Fallback to single query
                sub_queries = [SubQuery(prompt, 1, "general", prompt[:500])]
            
            # Phase 4: Multi-agent parallel execution
            agent_results = []
            
            if len(sub_queries) > 1:
                # Parallel execution for multiple sub-queries
                with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_sub_agents) as executor:
                    future_to_query = {}
                    
                    for i, sub_query in enumerate(sub_queries[:self.max_sub_agents]):
                        agent = ResearchAgent(f"agent_{i+1}", self.openai_client, self.search_client, self.logger)
                        future = executor.submit(agent.conduct_specialized_research, sub_query)
                        future_to_query[future] = sub_query
                    
                    for future in concurrent.futures.as_completed(future_to_query, timeout=self.parallel_execution_timeout):
                        try:
                            result = future.result()
                            agent_results.append(result)
                        except Exception as e:
                            self.logger.error(f"Agent execution error: {e}")
            else:
                # Single agent execution
                agent = ResearchAgent("agent_1", self.openai_client, self.search_client, self.logger)
                result = agent.conduct_specialized_research(sub_queries[0])
                agent_results.append(result)
            
            # Phase 4: Synthesis and integration
            final_content = self._synthesize_agent_results(agent_results)
            
            # Collect all sources
            all_sources = []
            for result in agent_results:
                all_sources.extend(result.sources)
            
            return {
                'content': final_content,
                'search_results': all_sources,
                'agent_results': len(agent_results),
                'confidence_score': sum(r.confidence_score for r in agent_results) / len(agent_results) if agent_results else 0.0
            }
            
        except concurrent.futures.TimeoutError:
            self.logger.error("Multi-agent execution timeout")
            return None
        except Exception as e:
            self.logger.error(f"LangChain research failed: {e}")
            return None
    
    def _synthesize_agent_results(self, agent_results: List[AgentResult]) -> str:
        """Synthesize multiple agent results into final report"""
        if not agent_results:
            return "研究結果の統合に失敗しました。"
        
        if len(agent_results) == 1:
            return agent_results[0].content
        
        # Multi-agent synthesis
        synthesis_prompt = f"""
        以下の複数の専門エージェントによる研究結果を統合し、包括的で洞察に富んだ最終レポートを作成してください。

        エージェント研究結果:
        """
        
        for i, result in enumerate(agent_results, 1):
            synthesis_prompt += f"""
        
        ## エージェント{i} - {result.domain}分野 (信頼度: {result.confidence_score:.2f})
        研究クエリ: {result.query}
        
        {result.content}
        
        ---
        """
        
        synthesis_prompt += """
        
        上記の結果を統合して、以下の構造で包括的なレポートを作成してください：
        
        # 統合研究レポート
        
        ## エグゼクティブサマリー
        ## 主要な発見事項
        ## 分野横断的な洞察
        ## 実装・実践への提言
        ## 今後の研究課題
        
        各エージェントの専門知識を活かし、相互の関連性や矛盾点も明記してください。
        """
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": synthesis_prompt}],
                max_tokens=3000,
                temperature=0.5
            )
            
            synthesized_content = response.choices[0].message.content
            
            # Add agent performance summary
            agent_summary = "\n\n## 研究実行詳細\n\n"
            agent_summary += f"- 実行エージェント数: {len(agent_results)}\n"
            agent_summary += f"- 平均信頼度スコア: {sum(r.confidence_score for r in agent_results) / len(agent_results):.2f}\n"
            agent_summary += "- 専門分野: " + ", ".join([r.domain for r in agent_results]) + "\n"
            
            return synthesized_content + agent_summary
            
        except Exception as e:
            self.logger.error(f"Synthesis failed: {e}")
            # Fallback: simple concatenation
            fallback_content = "# 統合研究レポート\n\n"
            for i, result in enumerate(agent_results, 1):
                fallback_content += f"## {result.domain}分野の分析\n\n{result.content}\n\n"
            return fallback_content