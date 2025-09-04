#!/usr/bin/env python3
"""
自動リサーチシステム
Obsidian日記から注目ワードを抽出し、Perplexity APIでリサーチを実行して結果を保存する
"""

import os
import requests
import json
from datetime import datetime, timedelta
import logging
import re
from typing import List, Optional, Dict

class AutoResearchSystem:
    def __init__(self, config_path: str = ".env"):
        """初期化"""
        self.config = self._load_config(config_path)
        self.setup_logging()
        
    def _load_config(self, config_path: str) -> Dict[str, str]:
        """設定ファイル読み込み"""
        config = {}
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                for line in f:
                    if '=' in line and not line.startswith('#'):
                        key, value = line.strip().split('=', 1)
                        config[key] = value.strip('"\'')
        return config
    
    def setup_logging(self):
        """ログ設定"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('auto_research.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def get_diary_files(self, days_back: int = 1) -> List[str]:
        """Obsidian日記ファイルのパスを取得"""
        # 環境変数から直接取得
        diary_base_path = os.environ.get('USER_INFO_PATH') or self.config.get('USER_INFO_PATH')
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
        # 環境変数から直接取得
        prompt_file_path = os.environ.get('PROMPT_TEMPLATE_PATH') or self.config.get('PROMPT_TEMPLATE_PATH')
        
        if not os.path.exists(prompt_file_path):
            self.logger.error(f"Prompt template file not found: {prompt_file_path}")
            self.logger.error("Stopping execution to avoid unnecessary API costs")
            return False
        return True
    
    def read_prompt_template(self) -> str:
        """プロンプトテンプレートファイルを読み込み"""
        # 環境変数から直接取得
        prompt_file_path = os.environ.get('PROMPT_TEMPLATE_PATH') or self.config.get('PROMPT_TEMPLATE_PATH')
        
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
    
    def call_perplexity_api(self, prompt: str) -> Optional[str]:
        """Perplexity APIを呼び出し"""
        api_key = self.config.get('PERPLEXITY_API_KEY')
        if not api_key:
            self.logger.error("PERPLEXITY_API_KEY not found in config")
            return None
        
        url = "https://api.perplexity.ai/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "sonar-deep-research",
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "reasoning_effort": "medium",
            "temperature": 0.7,
            "max_tokens": 8192
        }
        
        try:
            self.logger.info("Calling Perplexity API...")
            response = requests.post(url, headers=headers, json=data, timeout=1200)
            response.raise_for_status()
            
            result = response.json()
            if 'choices' in result and len(result['choices']) > 0:
                content = result['choices'][0]['message']['content']
                # search_resultsも一緒に返す
                search_results = result.get('search_results', [])
                return {'content': content, 'search_results': search_results}
            else:
                self.logger.error("Unexpected API response format")
                return None
                
        except requests.exceptions.RequestException as e:
            self.logger.error(f"API request failed: {e}")
            return None
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON decode error: {e}")
            return None
    
    def save_research_report(self, api_response) -> str:
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
        
        # 環境変数から直接取得
        output_dir = os.environ.get('RESEARCH_REPORT_PATH') or self.config.get('RESEARCH_REPORT_PATH')
        
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
        
        # Markdownコンテンツ作成
        markdown_content = f"""# 自動リサーチレポート - {today}

生成日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

{content}{citation_list}

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
            
            # 5. API呼び出し
            research_result = self.call_perplexity_api(prompt)
            if not research_result:
                self.logger.error("Failed to get research result from API")
                return
            
            # 6. レポート保存
            report_path = self.save_research_report(research_result)
            if report_path:
                self.logger.info(f"Auto research completed successfully: {report_path}")
            else:
                self.logger.error("Failed to save research report")
                
        except Exception as e:
            self.logger.error(f"Unexpected error in main process: {e}")

def main():
    """メイン関数"""
    system = AutoResearchSystem()
    system.run()

if __name__ == "__main__":
    main()