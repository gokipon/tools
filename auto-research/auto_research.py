#!/usr/bin/env python3
"""
自動リサーチシステム - Provider パターン版
Obsidian日記から注目ワードを抽出し、選択されたProviderでリサーチを実行して結果を保存する

支援するProvider:
- Perplexity API (既存)
- LangChain + Azure OpenAI (新規: Phase 2-4 multi-agent system)
"""

import os
import argparse
from datetime import datetime, timedelta
import logging
import re
from typing import List, Optional, Dict

from providers.factory import ProviderFactory
from providers.base import ResearchProvider

class AutoResearchSystem:
    def __init__(self, provider_type: str = "perplexity", config_path: str = None, debug: bool = False):
        """
        初期化
        
        Args:
            provider_type: 使用するプロバイダー ('perplexity' or 'langchain')
            config_path: カスタム設定ファイルのパス
            debug: デバッグモード
        """
        self.provider_type = provider_type
        self.debug = debug
        self.config = self._load_hierarchical_config(config_path)
        self.setup_logging()
        self.provider = self._create_provider()
        
    def _load_hierarchical_config(self, custom_config_path: str = None) -> Dict[str, str]:
        """
        階層的設定読み込み (CLI > custom.env > provider.env > .env > default)
        """
        config = {}
        
        # 1. Default .env file
        self._load_config_file(".env", config)
        
        # 2. Provider-specific config
        provider_config_path = f"config/{self.provider_type}.env"
        if os.path.exists(provider_config_path):
            self._load_config_file(provider_config_path, config)
        
        # 3. Custom config file if specified
        if custom_config_path and os.path.exists(custom_config_path):
            self._load_config_file(custom_config_path, config)
        
        # 4. Environment variables override
        for key in config.keys():
            env_value = os.getenv(key)
            if env_value:
                config[key] = env_value
        
        return config
    
    def _load_config_file(self, config_path: str, config: Dict[str, str]):
        """単一設定ファイル読み込み"""
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if '=' in line and not line.startswith('#'):
                        key, value = line.strip().split('=', 1)
                        config[key] = value.strip('"\'')
    
    def _create_provider(self) -> ResearchProvider:
        """プロバイダー作成"""
        try:
            return ProviderFactory.create_provider(self.provider_type, self.config, self.logger)
        except ValueError as e:
            self.logger.error(f"Provider creation failed: {e}")
            raise
    
    def setup_logging(self):
        """ログ設定"""
        log_level = logging.DEBUG if self.debug else logging.INFO
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('auto_research.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Using provider: {self.provider_type}")
    
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
    
    def conduct_research(self, prompt: str) -> Optional[Dict]:
        """選択されたプロバイダーでリサーチを実行"""
        self.logger.info(f"Conducting research with {self.provider.get_provider_name()} provider...")
        
        if self.debug:
            self.logger.debug(f"Prompt length: {len(prompt)} characters")
            self.logger.debug(f"First 200 chars of prompt: {prompt[:200]}...")
        
        return self.provider.conduct_research(prompt)
    
    def save_research_report(self, api_response) -> str:
        """リサーチレポートをMarkdownファイルとして保存"""
        # APIレスポンスの形式に応じて処理
        if isinstance(api_response, str):
            # 文字列の場合（後方互換性）
            content = api_response
            search_results = []
            metadata = {}
        elif isinstance(api_response, dict):
            # 辞書の場合（新形式）
            content = api_response.get('content', '')
            search_results = api_response.get('search_results', [])
            metadata = {
                'agent_results': api_response.get('agent_results', 1),
                'confidence_score': api_response.get('confidence_score', 0.0),
                'provider': self.provider.get_provider_name()
            }
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
        
        # メタデータセクション作成
        metadata_section = ""
        if metadata:
            metadata_section = f"""
## 生成メタデータ

- **プロバイダー**: {metadata.get('provider', 'Unknown')}
- **エージェント数**: {metadata.get('agent_results', 1)}
- **信頼度スコア**: {metadata.get('confidence_score', 0.0):.2f}
"""

        # Markdownコンテンツ作成
        markdown_content = f"""# 自動リサーチレポート - {today}

生成日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
{metadata_section}
---

{content}{citation_list}

---

*このレポートは自動リサーチシステム (Provider: {self.provider.get_provider_name()}) によって生成されました*
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
        self.logger.info("Starting auto research system...")
        
        try:
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
            
            # 5. リサーチ実行
            research_result = self.conduct_research(prompt)
            if not research_result:
                self.logger.error(f"Failed to get research result from {self.provider.get_provider_name()} provider")
                return
            
            # 6. レポート保存
            report_path = self.save_research_report(research_result)
            if report_path:
                self.logger.info(f"Auto research completed successfully: {report_path}")
            else:
                self.logger.error("Failed to save research report")
                
        except Exception as e:
            self.logger.error(f"Unexpected error in main process: {e}")

def create_argument_parser():
    """コマンドライン引数パーサー作成"""
    parser = argparse.ArgumentParser(
        description='自動リサーチシステム - Provider パターン版',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  python auto_research.py                                    # デフォルト (Perplexity)
  python auto_research.py --provider perplexity             # Perplexity明示
  python auto_research.py --provider langchain              # LangChain + Azure OpenAI
  python auto_research.py -p langchain --config custom.env  # カスタム設定
  python auto_research.py --list-providers                  # 利用可能プロバイダー一覧
  python auto_research.py --debug                           # デバッグモード

プロバイダー:
  perplexity: Perplexity API (既存システム)
  langchain:  LangChain + Azure OpenAI + Multi-agent system (Phase 2-4)
        """
    )
    
    parser.add_argument(
        '--provider', '-p',
        choices=['perplexity', 'langchain'],
        default='perplexity',
        help='使用するリサーチプロバイダー (default: perplexity)'
    )
    
    parser.add_argument(
        '--config', '-c',
        type=str,
        help='カスタム設定ファイルのパス'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='デバッグモードでログ出力を詳細化'
    )
    
    parser.add_argument(
        '--list-providers',
        action='store_true',
        help='利用可能なプロバイダー一覧を表示'
    )
    
    return parser

def main():
    """メイン関数"""
    parser = create_argument_parser()
    args = parser.parse_args()
    
    # プロバイダー一覧表示
    if args.list_providers:
        available_providers = ProviderFactory.get_available_providers()
        print("利用可能なリサーチプロバイダー:")
        for provider in available_providers:
            print(f"  - {provider}")
        return
    
    try:
        # システム初期化
        system = AutoResearchSystem(
            provider_type=args.provider,
            config_path=args.config,
            debug=args.debug
        )
        
        # リサーチ実行
        system.run()
        
    except KeyboardInterrupt:
        print("\n操作が中断されました。")
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    main()