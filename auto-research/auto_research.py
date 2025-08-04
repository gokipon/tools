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
    
    def get_diary_files(self, days_back: int = 2) -> List[str]:
        """Obsidian日記ファイルのパスを取得"""
        diary_base_path = self.config.get('DIARY_PATH', '/Users/haruki/Library/Mobile Documents/iCloud~md~obsidian/Documents/I-think-therefore-I-am/diary')
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
    
    def read_prompt_template(self) -> str:
        """プロンプトテンプレートファイルを読み込み"""
        prompt_file_path = self.config.get('PROMPT_FILE_PATH', 
            '/Users/haruki/Library/Mobile Documents/iCloud~md~obsidian/Documents/I-think-therefore-I-am/knowledge/インプット体系/情報取得の仕組み.md')
        
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
            response = requests.post(url, headers=headers, json=data, timeout=120)
            response.raise_for_status()
            
            result = response.json()
            if 'choices' in result and len(result['choices']) > 0:
                return result['choices'][0]['message']['content']
            else:
                self.logger.error("Unexpected API response format")
                return None
                
        except requests.exceptions.RequestException as e:
            self.logger.error(f"API request failed: {e}")
            return None
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON decode error: {e}")
            return None
    
    def save_research_report(self, content: str) -> str:
        """リサーチレポートをMarkdownファイルとして保存"""
        output_dir = self.config.get('OUTPUT_DIR', 
            '/Users/haruki/Library/Mobile Documents/iCloud~md~obsidian/Documents/I-think-therefore-I-am/artifact/research-report')
        
        # ディレクトリ作成
        os.makedirs(output_dir, exist_ok=True)
        
        # ファイル名生成
        today = datetime.now().strftime('%Y-%m-%d')
        filename = f"{today}.md"
        filepath = os.path.join(output_dir, filename)
        
        # Markdownコンテンツ作成
        markdown_content = f"""# 自動リサーチレポート - {today}

生成日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

{content}

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
            
            # 3. プロンプト生成
            prompt = self.generate_research_prompt(diary_content)
            
            # 4. API呼び出し
            research_result = self.call_perplexity_api(prompt)
            if not research_result:
                self.logger.error("Failed to get research result from API")
                return
            
            # 5. レポート保存
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