#!/usr/bin/env python3
"""
自動リサーチシステム
Provider パターンによる拡張可能自動リサーチシステム

Obsidian日記から注目ワードを抽出し、選択したProviderでリサーチを実行して結果を保存する

使用例:
    # デフォルト (Perplexity - 後方互換性維持)
    python auto_research.py

    # Provider明示指定
    python auto_research.py --provider perplexity
    python auto_research.py --provider langchain
    python auto_research.py -p langchain --config custom.env --debug
"""

import os
import argparse
import json
from datetime import datetime, timedelta
import logging
import re
from typing import List, Optional, Dict

from providers import ResearchProvider, PerplexityProvider, LangChainProvider

class ProviderFactory:
    """Provider Factory for creating research providers"""
    
    @staticmethod
    def create_provider(provider_type: str, config: Dict[str, str], logger: logging.Logger) -> ResearchProvider:
        """
        Create a research provider instance
        
        Args:
            provider_type: Type of provider ('perplexity' or 'langchain')
            config: Configuration dictionary
            logger: Logger instance
            
        Returns:
            ResearchProvider instance
            
        Raises:
            ValueError: If provider type is unknown
        """
        if provider_type == "perplexity":
            return PerplexityProvider(config, logger)
        elif provider_type == "langchain":
            if LangChainProvider is None:
                raise ValueError("LangChain provider not available. Install required dependencies.")
            return LangChainProvider(config, logger)
        else:
            raise ValueError(f"Unknown provider type: {provider_type}. Available providers: perplexity, langchain")

class AutoResearchSystem:
    def __init__(self, provider_type: str = "perplexity", config_path: str = None, debug: bool = False):
        """
        初期化
        
        Args:
            provider_type: Provider type ('perplexity' or 'langchain')
            config_path: Path to config file (defaults to provider-specific or .env)
            debug: Enable debug logging
        """
        self.provider_type = provider_type
        
        # Determine config path with priority: CLI > provider.env > .env
        if config_path:
            self.config_path = config_path
        elif provider_type == "langchain":
            # Look for langchain-specific config
            if os.path.exists("config/langchain.env"):
                self.config_path = "config/langchain.env"
            elif os.path.exists("langchain.env"):
                self.config_path = "langchain.env"
            else:
                self.config_path = ".env"
        else:
            self.config_path = ".env"
        
        self.config = self._load_config(self.config_path)
        self.setup_logging(debug)
        
        # Create provider using factory
        try:
            self.provider = ProviderFactory.create_provider(provider_type, self.config, self.logger)
            self.logger.info(f"Initialized {self.provider.get_provider_name()} provider")
        except ValueError as e:
            self.logger.error(f"Failed to create provider: {e}")
            raise
        
    def _load_config(self, config_path: str) -> Dict[str, str]:
        """設定ファイル読み込み"""
        config = {}
        if os.path.exists(config_path):
            self.logger.info(f"Loading config from: {config_path}") if hasattr(self, 'logger') else None
            with open(config_path, 'r') as f:
                for line in f:
                    if '=' in line and not line.startswith('#'):
                        key, value = line.strip().split('=', 1)
                        config[key] = value.strip('"\'')
        elif config_path != ".env":
            # Only warn if non-default config path was specified
            print(f"Warning: Config file not found: {config_path}")
        return config
    
    def setup_logging(self, debug: bool = False):
        """ログ設定"""
        log_level = logging.DEBUG if debug else logging.INFO
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('auto_research.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        if debug:
            self.logger.debug(f"Debug mode enabled")
            self.logger.debug(f"Provider: {self.provider_type}")
            self.logger.debug(f"Config path: {self.config_path}")
    
    def get_diary_files(self, days_back: int = 1) -> List[str]:
        """Obsidian日記ファイルのパスを取得"""
        # load-env.shで検証済みの環境変数を使用
        diary_base_path = self.config.get('USER_INFO_PATH')
        diary_files = []
        
        for i in range(1, days_back + 1):
            target_date = datetime.now() - timedelta(days=i)
            year = target_date.strftime('%Y')
            month = target_date.strftime('%m')
            date_str = target_date.strftime('%Y-%m-%d')
            
            diary_path = os.path.join(diary_base_path, year, month, f"{date_str}.md")
            if os.path.exists(diary_path):
                diary_files.append(diary_path)
                self.logger.info(f"Found diary file: {diary_path}")
        
        return diary_files
    
    def read_diary_content(self, diary_files: List[str]) -> str:
        """日記内容を読み込み"""
        content = ""
        total_chars = 0
        
        for diary_file in diary_files:
            try:
                with open(diary_file, 'r', encoding='utf-8') as f:
                    file_content = f.read()
                    content += f"\n\n=== {os.path.basename(diary_file)} ===\n{file_content}"
                    total_chars += len(file_content)
                    
                    # 前日の日記が3000文字以上の場合、前々日は不要
                    if diary_file == diary_files[0] and total_chars >= 3000:
                        self.logger.info(f"Previous day diary has {total_chars} characters, skipping older entries")
                        break
                        
            except Exception as e:
                self.logger.error(f"Error reading {diary_file}: {e}")
        
        return content.strip()
    
    def check_prompt_template_exists(self) -> bool:
        """プロンプトテンプレートファイルの存在チェック"""
        # load-env.shで検証済みの環境変数を使用
        prompt_file_path = self.config.get('PROMPT_TEMPLATE_PATH')
        
        if not os.path.exists(prompt_file_path):
            self.logger.error(f"Prompt template file not found: {prompt_file_path}")
            self.logger.error("Stopping execution to avoid unnecessary API costs")
            return False
        return True
    
    def read_prompt_template(self) -> str:
        """プロンプトテンプレートファイルを読み込み"""
        # load-env.shで検証済みの環境変数を使用
        prompt_file_path = self.config.get('PROMPT_TEMPLATE_PATH')
        
        try:
            with open(prompt_file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            self.logger.error(f"Error reading prompt template file: {e}")
            return ""
    
    def generate_research_prompt(self, diary_content: str) -> str:
        """日記内容とプロンプトテンプレートからリサーチプロンプトを生成"""
        prompt_template = self.read_prompt_template()
        
        if not prompt_template:
            # フォールバック用のデフォルトプロンプト
            prompt_template = """
私の情報をもとに以下の観点で情報を収集してください：
- 私が抱えるコアな課題（ペイン）に効く
- 私が想定している社会の未来像における、直近の進捗が分かる
- 私が持つ興味に刺さる
その上で行動を提示してください。
"""
        
        combined_prompt = f"""
{prompt_template}

## 私の最近の日記内容（情報源）：
{diary_content}

"""
        
        return combined_prompt
    
    def save_research_report(self, api_response: Dict[str, any]) -> str:
        """リサーチレポートをMarkdownファイルとして保存"""
        # APIレスポンスの形式に応じて処理
        if isinstance(api_response, str):
            # 文字列の場合（後方互換性）
            content = api_response
            search_results = []
        elif isinstance(api_response, dict):
            # 辞書の場合（新形式）
            content = api_response.get('content', '')
            search_results = api_response.get('search_results', [])
        else:
            self.logger.error("Invalid API response format")
            return ""
        
        # load-env.shで検証済みの環境変数を使用
        output_dir = self.config.get('RESEARCH_REPORT_PATH')
        
        # ディレクトリ作成
        os.makedirs(output_dir, exist_ok=True)
        
        # ファイル名生成
        today = datetime.now().strftime('%Y-%m-%d')
        filename = f"{today}.md"
        filepath = os.path.join(output_dir, filename)
        
        # 文章中の引用をクリック可能なリンクに変換
        if search_results:
            def replace_citation(match):
                citation_num = int(match.group(1))
                if 1 <= citation_num <= len(search_results):
                    url = search_results[citation_num - 1].get('url', '')
                    if url:
                        return f'[{citation_num}]({url})'
                return match.group(0)  # 元のまま
            
            # [数字] のパターンを置換
            citation_pattern = r'\[(\d+)\]'
            content = re.sub(citation_pattern, replace_citation, content)
        
        # 参考文献リストを追加
        citation_list = ""
        if search_results:
            citation_list = "\n\n## 参考文献\n\n"
            for i, result in enumerate(search_results, 1):
                title = result.get('title', f'Source {i}')
                url = result.get('url', '')
                if url:
                    citation_list += f"{i}. [{title}]({url})\n"
        
        # Provider情報を追加
        provider_info = f"\n\n---\n\n*Provider: {self.provider.get_provider_name()}*"
        
        # Markdownコンテンツ作成
        markdown_content = f"""# 自動リサーチレポート - {today}

生成日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

{content}{citation_list}{provider_info}

---

*このレポートは自動リサーチシステムによって生成されました*
"""
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            
            self.logger.info(f"Research report saved: {filepath}")
            return filepath
            
        except Exception as e:
            self.logger.error(f"Error saving report: {e}")
            return ""
    
    def run(self):
        """メイン処理実行"""
        self.logger.info(f"Starting auto research system with {self.provider.get_provider_name()} provider...")
        
        try:
            # Provider設定検証
            if not self.provider.validate_config():
                self.logger.error(f"Provider configuration validation failed")
                return
            
            # 1. 日記ファイル取得
            diary_files = self.get_diary_files()
            if not diary_files:
                self.logger.warning("No diary files found")
                return
            
            # 2. 日記内容読み込み
            diary_content = self.read_diary_content(diary_files)
            if not diary_content:
                self.logger.warning("No diary content found")
                return
            
            # 3. プロンプトテンプレートファイル存在チェック（API呼び出し前に実行）
            if not self.check_prompt_template_exists():
                self.logger.error("Prompt template file missing - aborting to prevent API costs")
                return
            
            # 4. プロンプト生成
            prompt = self.generate_research_prompt(diary_content)
            
            # 5. Provider経由でリサーチ実行
            research_result = self.provider.conduct_research(prompt)
            if not research_result:
                self.logger.error("Failed to get research result from provider")
                return
            
            # 6. レポート保存
            report_path = self.save_research_report(research_result)
            if report_path:
                self.logger.info(f"Auto research completed successfully: {report_path}")
            else:
                self.logger.error("Failed to save research report")
                
        except Exception as e:
            self.logger.error(f"Unexpected error in main process: {e}")

def parse_arguments():
    """コマンドライン引数をパース"""
    parser = argparse.ArgumentParser(
        description="拡張可能自動リサーチシステム",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
    # デフォルト (Perplexity - 後方互換性維持)
    python auto_research.py

    # Provider明示指定
    python auto_research.py --provider perplexity
    python auto_research.py --provider langchain
    
    # 設定ファイル指定
    python auto_research.py -p langchain --config custom.env --debug

利用可能なProviders:
    perplexity  - Perplexity API (既存システム、デフォルト)
    langchain   - LangChain with Azure OpenAI (Phase 2-4で段階実装)
        """
    )
    
    parser.add_argument(
        '--provider', '-p',
        choices=['perplexity', 'langchain'],
        default='perplexity',
        help='Research provider to use (default: perplexity)'
    )
    
    parser.add_argument(
        '--config', '-c',
        type=str,
        help='Path to configuration file (default: provider-specific or .env)'
    )
    
    parser.add_argument(
        '--debug', '-d',
        action='store_true',
        help='Enable debug logging'
    )
    
    parser.add_argument(
        '--list-providers',
        action='store_true',
        help='List available providers and exit'
    )
    
    return parser.parse_args()

def main():
    """メイン関数"""
    args = parse_arguments()
    
    if args.list_providers:
        print("Available research providers:")
        print("  perplexity  - Perplexity API (既存システム)")
        print("  langchain   - LangChain with Azure OpenAI (Phase 2-4で段階実装)")
        return
    
    try:
        system = AutoResearchSystem(
            provider_type=args.provider,
            config_path=args.config,
            debug=args.debug
        )
        system.run()
    except Exception as e:
        print(f"Failed to initialize system: {e}")
        return 1

if __name__ == "__main__":
    main()