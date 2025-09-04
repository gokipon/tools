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

from pydantic import BaseModel

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

# Pydantic models for structured outputs
class SubQuery(BaseModel):
    query: str
    priority: int
    domain: str
    context: str = ""

class QueryDecomposition(BaseModel):
    sub_queries: List[SubQuery]

class ResearchContent(BaseModel):
    current_analysis: str
    key_findings: str
    implementation_insights: str
    future_prospects: str

class AgentResult(BaseModel):
    agent_id: str
    query: str
    content: ResearchContent
    sources: List[Dict[str, Any]]
    confidence_score: float
    domain: str

class FinalReport(BaseModel):
    executive_summary: str
    main_findings: str
    cross_domain_insights: str
    actionable_recommendations: str
    future_research_topics: str

class ResearchSupervisor:
    """Supervisor for multi-agent research coordination"""
    
    def __init__(self, openai_client, logger, config=None):
        self.client = openai_client
        self.logger = logger
        self.config = config
    
    def _load_prompt_template(self, config_key: str, fallback_content: str = "") -> str:
        """Load prompt template from file"""
        prompt_path = self.config.get(config_key)
        if not prompt_path:
            self.logger.warning(f"Prompt path {config_key} not found in config, using fallback")
            return fallback_content
        
        try:
            with open(prompt_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                self.logger.debug(f"Loaded prompt template from {prompt_path}")
                return content
        except Exception as e:
            self.logger.error(f"Failed to load prompt template {prompt_path}: {e}")
            return fallback_content
    
    def decompose_query(self, query: str, context: str) -> List[SubQuery]:
        """Decompose main query into sub-queries for parallel processing"""
        # Load prompt template from file
        prompt_template = self._load_prompt_template(
            'QUERY_DECOMPOSITION_PROMPT_PATH',
            """あなたは研究戦略の専門家です。以下のメインクエリと文脈を分析し、並列処理可能な3つの専門的なサブクエリに分解してください。

メインクエリ: {query}

文脈: {context}

各サブクエリは以下の形式で出力してください：
1. [ドメイン名] クエリ内容 (優先度: 1-3)
2. [ドメイン名] クエリ内容 (優先度: 1-3)  
3. [ドメイン名] クエリ内容 (優先度: 1-3)

ドメイン例: 技術動向, 市場分析, 学術研究, 実装手法, 将来展望など
優先度: 1=最重要, 2=重要, 3=補足"""
        )
        
        decomposition_prompt = prompt_template.format(query=query, context=context)
        
        try:
            response = self.client.beta.chat.completions.parse(
                model=self.config.get('AZURE_OPENAI_DEPLOYMENT', 'gpt-4'),
                messages=[{"role": "user", "content": decomposition_prompt}],
                response_format=QueryDecomposition,
                max_completion_tokens=int(self.config.get('MAX_COMPLETION_TOKENS', 3000)),
                temperature=1
            )
            
            decomposition = response.choices[0].message.parsed
            if decomposition and decomposition.sub_queries:
                return decomposition.sub_queries[:3]  # Limit to 3 sub-queries
            
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
            
            # Fallback to default decomposition
            self.logger.warning("Query decomposition failed, using fallback")
            return [
                SubQuery(query="技術動向と最新の進展", priority=1, domain="技術動向", context=context[:500]),
                SubQuery(query="実用化・実装における課題と解決策", priority=2, domain="実装手法", context=context[:500]),
                SubQuery(query="将来の展望と影響分析", priority=2, domain="将来展望", context=context[:500])
            ]
            
            return sub_queries[:3]  # Limit to 3 sub-queries
            
        except Exception as e:
            self.logger.error(f"Error in query decomposition: {e}")
            # Fallback
            return [
                SubQuery(query="技術動向と最新の進展", priority=1, domain="技術動向", context=context[:500]),
                SubQuery(query="実用化・実装における課題と解決策", priority=2, domain="実装手法", context=context[:500]),
                SubQuery(query="将来の展望と影響分析", priority=2, domain="将来展望", context=context[:500])
            ]

class ContextCompressor:
    """Context compression for token optimization"""
    
    def __init__(self, openai_client, logger, config=None):
        self.client = openai_client
        self.logger = logger
        self.config = config
    
    def _load_prompt_template(self, config_key: str, fallback_content: str = "") -> str:
        """Load prompt template from file"""
        prompt_path = self.config.get(config_key)
        if not prompt_path:
            self.logger.warning(f"Prompt path {config_key} not found in config, using fallback")
            return fallback_content
        
        try:
            with open(prompt_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                self.logger.debug(f"Loaded prompt template from {prompt_path}")
                return content
        except Exception as e:
            self.logger.error(f"Failed to load prompt template {prompt_path}: {e}")
            return fallback_content
    
    def compress_context(self, context: str, threshold: int = 4000) -> str:
        """Compress context if it exceeds threshold"""
        if len(context) <= threshold:
            return context
        
        # Load prompt template from file
        prompt_template = self._load_prompt_template(
            'CONTEXT_COMPRESSION_PROMPT_PATH',
            """以下の長いコンテンツを{threshold}文字程度に要約してください。重要な情報を保持し、研究に必要な文脈を維持してください。

コンテンツ:
{context}"""
        )
        
        compression_prompt = prompt_template.format(threshold=threshold//2, context=context)
        
        try:
            response = self.client.chat.completions.create(
                model=self.config.get('AZURE_OPENAI_DEPLOYMENT', 'gpt-4'),
                messages=[{"role": "user", "content": compression_prompt}],
                max_completion_tokens=1000,
                temperature=1
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
    
    def __init__(self, agent_id: str, openai_client, search_client, logger, config=None):
        self.agent_id = agent_id
        self.openai_client = openai_client
        self.search_client = search_client
        self.logger = logger
        self.config = config
    
    def _load_prompt_template(self, config_key: str, fallback_content: str = "") -> str:
        """Load prompt template from file"""
        prompt_path = self.config.get(config_key)
        if not prompt_path:
            self.logger.warning(f"Prompt path {config_key} not found in config, using fallback")
            return fallback_content
        
        try:
            with open(prompt_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                self.logger.debug(f"Loaded prompt template from {prompt_path}")
                return content
        except Exception as e:
            self.logger.error(f"Failed to load prompt template {prompt_path}: {e}")
            return fallback_content
    
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
                    search_depth="advanced",
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
        
        # Load prompt template from file
        prompt_template = self._load_prompt_template(
            'RESEARCH_AGENT_PROMPT_PATH',
            """あなたは{domain}の専門研究者です。以下の専門的な観点から詳細な分析を行ってください。

研究クエリ: {query}

文脈: {context}
{search_context}

以下の構造で回答してください：
## 現状分析
## 重要な発見・トレンド
## 実用化への示唆
## 今後の展望

専門性を活かした深い洞察と具体的な行動提案を含めてください。"""
        )
        
        research_prompt = prompt_template.format(
            domain=sub_query.domain,
            query=sub_query.query,
            context=sub_query.context,
            search_context=search_context
        )
        
        try:
            response = self.openai_client.beta.chat.completions.parse(
                model=self.config.get('AZURE_OPENAI_DEPLOYMENT', 'gpt-4') if self.config else 'gpt-4',
                messages=[{"role": "user", "content": research_prompt}],
                response_format=ResearchContent,
                max_completion_tokens=int(self.config.get('MAX_COMPLETION_TOKENS', 3000)),
                temperature=1
            )
            
            research_content = response.choices[0].message.parsed
            if research_content:
                content = f"""## 現状分析
{research_content.current_analysis}

## 重要な発見・トレンド
{research_content.key_findings}

## 実用化への示唆
{research_content.implementation_insights}

## 今後の展望
{research_content.future_prospects}
"""
            else:
                content = "構造化出力の解析に失敗しました"
            
            # Calculate confidence score based on search results and content quality
            confidence_score = 0.7  # Base score
            if search_results:
                confidence_score += 0.2
            if len(content) > 1000:
                confidence_score += 0.1
            
            return AgentResult(
                agent_id=self.agent_id,
                query=sub_query.query,
                content=research_content if research_content else ResearchContent(
                    current_analysis=content,
                    key_findings="",
                    implementation_insights="",
                    future_prospects=""
                ),
                sources=sources,
                confidence_score=min(confidence_score, 1.0),
                domain=sub_query.domain
            )
            
        except Exception as e:
            self.logger.error(f"Agent {self.agent_id} research failed: {e}")
            return AgentResult(
                agent_id=self.agent_id,
                query=sub_query.query,
                content=ResearchContent(
                    current_analysis=f"研究中にエラーが発生しました: {str(e)}",
                    key_findings="",
                    implementation_insights="",
                    future_prospects=""
                ),
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
            self.supervisor = ResearchSupervisor(self.openai_client, logger, config)
            self.compressor = ContextCompressor(self.openai_client, logger, config)
        
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
                base_url=f"{base_url}openai/v1/"
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
    
    def _load_prompt_template(self, config_key: str, fallback_content: str = "") -> str:
        """Load prompt template from file"""
        prompt_path = self.config.get(config_key)
        if not prompt_path:
            self.logger.warning(f"Prompt path {config_key} not found in config, using fallback")
            return fallback_content
        
        try:
            with open(prompt_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                self.logger.debug(f"Loaded prompt template from {prompt_path}")
                return content
        except Exception as e:
            self.logger.error(f"Failed to load prompt template {prompt_path}: {e}")
            return fallback_content
    
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
                        agent = ResearchAgent(f"agent_{i+1}", self.openai_client, self.search_client, self.logger, self.config)
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
                agent = ResearchAgent("agent_1", self.openai_client, self.search_client, self.logger, self.config)
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
        
        # Prepare agent results content
        agent_results_text = ""
        
        for i, result in enumerate(agent_results, 1):
            # Extract content from structured result
            if isinstance(result.content, ResearchContent):
                content_text = f"""## 現状分析
{result.content.current_analysis}

## 重要な発見・トレンド
{result.content.key_findings}

## 実用化への示唆
{result.content.implementation_insights}

## 今後の展望
{result.content.future_prospects}
"""
            else:
                content_text = str(result.content)
            
            agent_results_text += f"""
        
## エージェント{i} - {result.domain}分野 (信頼度: {result.confidence_score:.2f})
研究クエリ: {result.query}

{content_text}

---
"""
        
        # Load prompt template from file
        prompt_template = self._load_prompt_template(
            'SYNTHESIS_PROMPT_PATH',
            """以下の複数の専門エージェントによる研究結果を統合し、包括的で洞察に富んだ最終レポートを作成してください。

エージェント研究結果:
{agent_results}

上記の結果を統合して、以下の構造で包括的なレポートを作成してください：

# 統合研究レポート

## エグゼクティブサマリー
## 主要な発見事項
## 分野横断的な洞察
## 実装・実践への提言
## 今後の研究課題

各エージェントの専門知識を活かし、相互の関連性や矛盾点も明記してください。"""
        )
        
        synthesis_prompt = prompt_template.format(agent_results=agent_results_text)
        
        try:
            response = self.openai_client.beta.chat.completions.parse(
                model=self.config.get('AZURE_OPENAI_DEPLOYMENT', 'gpt-4'),
                messages=[{"role": "user", "content": synthesis_prompt}],
                response_format=FinalReport,
                max_completion_tokens=int(self.config.get('MAX_COMPLETION_TOKENS', 3000)),
                temperature=1
            )
            
            final_report = response.choices[0].message.parsed
            if final_report:
                synthesized_content = f"""# 統合研究レポート

## エグゼクティブサマリー
{final_report.executive_summary}

## 主要な発見事項
{final_report.main_findings}

## 分野横断的な洞察
{final_report.cross_domain_insights}

## 実装・実践への提言
{final_report.actionable_recommendations}

## 今後の研究課題
{final_report.future_research_topics}
"""
            else:
                synthesized_content = "統合レポートの生成に失敗しました"
            
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
                if isinstance(result.content, ResearchContent):
                    content_text = f"""## 現状分析
{result.content.current_analysis}

## 重要な発見・トレンド
{result.content.key_findings}

## 実用化への示唆
{result.content.implementation_insights}

## 今後の展望
{result.content.future_prospects}
"""
                else:
                    content_text = str(result.content)
                fallback_content += f"## {result.domain}分野の分析\n\n{content_text}\n\n"
            return fallback_content