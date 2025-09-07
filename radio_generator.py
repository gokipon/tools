#!/usr/bin/env python3
"""
ラジオ原稿自動生成システム (Radio Script Auto-Generation System)

This system processes research reports and generates radio talk scripts 
for each chapter using Azure OpenAI API with conversation history management.
"""

import os
import re
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import time
import requests
from openai import OpenAI


class RadioGeneratorConfig:
    """Configuration management for the radio generator."""
    
    def __init__(self, config_file: str = "radio_config.json"):
        self.config_file = config_file
        self.config = self.load_config()
    
    def load_config(self) -> Dict:
        """Load configuration from file or create default."""
        default_config = {
            "azure_openai": {
                "api_key_env": "AZURE_OPENAI_API_KEY",
                "base_url": "https://YOUR-RESOURCE-NAME.openai.azure.com/openai/v1/",
                "model": "gpt-4o"
            },
            "line": {
                "token_env": "LINE_NOTIFY_TOKEN",
                "api_url": "https://notify-api.line.me/api/notify"
            },
            "paths": {
                "research_report": "/Users/haruki/Library/Mobile Documents/iCloud~md~obsidian/Documents/I-think-therefore-I-am/artifact/research-report/{date}.md",
                "prompt_template": "/Users/haruki/Library/Mobile Documents/iCloud~md~obsidian/Documents/I-think-therefore-I-am/pt/ラジオ原稿作り.md",
                "output_base": "/Users/haruki/Library/Mobile Documents/iCloud~md~obsidian/Documents/I-think-therefore-I-am/artifact/radio"
            },
            "settings": {
                "chapter_marker": "#automation/research-chapter",
                "api_delay": 2,
                "max_retries": 3,
                "log_level": "INFO"
            }
        }
        
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logging.warning(f"Failed to load config file {self.config_file}: {e}")
                return default_config
        else:
            # Create default config file
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=2, ensure_ascii=False)
            return default_config
    
    def get(self, key_path: str, default=None):
        """Get configuration value using dot notation (e.g., 'azure_openai.api_key')."""
        keys = key_path.split('.')
        value = self.config
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value


class ChapterExtractor:
    """Extract chapter information from research reports."""
    
    def __init__(self, chapter_marker: str = "#automation/research-chapter"):
        self.chapter_marker = chapter_marker
    
    def extract_chapters(self, content: str) -> List[Dict[str, str]]:
        """
        Extract chapter information from markdown content.
        
        Returns:
            List of dictionaries with 'number', 'title', 'content' keys
        """
        chapters = []
        
        # Find the chapter marker
        marker_pos = content.find(self.chapter_marker)
        if marker_pos == -1:
            raise ValueError(f"Chapter marker '{self.chapter_marker}' not found in content")
        
        # Get content after marker
        after_marker = content[marker_pos + len(self.chapter_marker):]
        
        # Extract numbered chapters using regex
        # Pattern matches: 1. **Title** or 1. ****Title****
        chapter_pattern = r'(\d+)\.\s*\*{2,4}([^*\n]+)\*{2,4}'
        matches = re.findall(chapter_pattern, after_marker)
        
        if not matches:
            raise ValueError("No chapters found in the expected format")
        
        for number, title in matches:
            chapters.append({
                'number': int(number),
                'title': title.strip(),
                'content': f"第{number}章: {title.strip()}"
            })
        
        return chapters


class RadioScriptGenerator:
    """Generate radio scripts using Azure OpenAI API."""
    
    def __init__(self, config: RadioGeneratorConfig):
        self.config = config
        self.client = self._init_openai_client()
        self.conversation_history = []
        
    def _init_openai_client(self) -> OpenAI:
        """Initialize OpenAI client with Azure configuration."""
        api_key = os.getenv(self.config.get('azure_openai.api_key_env'))
        if not api_key:
            raise ValueError(f"Azure OpenAI API key not found in environment variable: {self.config.get('azure_openai.api_key_env')}")
        
        return OpenAI(
            api_key=api_key,
            base_url=self.config.get('azure_openai.base_url')
        )
    
    def load_prompt_template(self) -> str:
        """Load the prompt template from file."""
        template_path = self.config.get('paths.prompt_template')
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            logging.error(f"Prompt template file not found: {template_path}")
            return "あなたはラジオ番組のスクリプト作成者です。以下の章の内容を基に、魅力的なラジオトーク台本を作成してください。"
    
    def generate_script_for_chapter(self, chapter: Dict[str, str], 
                                  research_report: str, 
                                  is_first_chapter: bool = False) -> str:
        """
        Generate radio script for a specific chapter.
        
        Args:
            chapter: Chapter information dict
            research_report: Full research report content
            is_first_chapter: Whether this is the first chapter
            
        Returns:
            Generated radio script
        """
        try:
            if is_first_chapter:
                # First chapter: use full prompt template + research report
                prompt_template = self.load_prompt_template()
                user_message = f"{prompt_template}\n\n研究レポート:\n{research_report}\n\n最初の章から始めてください: {chapter['content']}"
                
                # Initialize conversation
                self.conversation_history = [
                    {"role": "system", "content": "あなたは経験豊富なラジオ番組制作者です。研究レポートを基に魅力的なラジオトーク台本を章ごとに作成します。各章の内容を深く理解し、聞き手が興味を持つような構成で台本を作成してください。"},
                    {"role": "user", "content": user_message}
                ]
            else:
                # Subsequent chapters: just say "次の章"
                self.conversation_history.append({
                    "role": "user", 
                    "content": "次の章をお願いします。"
                })
            
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=self.config.get('azure_openai.model'),
                messages=self.conversation_history,
                temperature=0.7
            )
            
            script_content = response.choices[0].message.content
            
            # Add assistant response to conversation history
            self.conversation_history.append({
                "role": "assistant",
                "content": script_content
            })
            
            # Rate limiting
            time.sleep(self.config.get('settings.api_delay', 2))
            
            return script_content
            
        except Exception as e:
            logging.error(f"Failed to generate script for chapter {chapter['number']}: {e}")
            raise
    
    def generate_all_scripts(self, chapters: List[Dict[str, str]], 
                           research_report: str) -> List[Dict[str, str]]:
        """Generate scripts for all chapters."""
        scripts = []
        
        for i, chapter in enumerate(chapters):
            is_first = (i == 0)
            logging.info(f"Generating script for chapter {chapter['number']}: {chapter['title']}")
            
            script_content = self.generate_script_for_chapter(
                chapter, research_report, is_first
            )
            
            scripts.append({
                'chapter': chapter,
                'script': script_content
            })
        
        return scripts


class FileManager:
    """Handle file operations for reading and writing."""
    
    def __init__(self, config: RadioGeneratorConfig):
        self.config = config
    
    def read_research_report(self, date: str = None) -> str:
        """Read research report from configured path."""
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        report_path = self.config.get('paths.research_report').format(date=date)
        
        try:
            with open(report_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if not content.strip():
                raise ValueError(f"Research report file is empty: {report_path}")
            
            return content
        except FileNotFoundError:
            raise FileNotFoundError(f"Research report not found: {report_path}")
    
    def sanitize_filename(self, filename: str) -> str:
        """Sanitize filename by removing/replacing special characters."""
        # Remove or replace problematic characters
        filename = re.sub(r'[<>:"/\\|?*]', '', filename)
        filename = filename.replace(' ', '_')
        return filename.strip()
    
    def save_chapter_script(self, chapter_data: Dict, script: str, 
                          output_dir: Path) -> str:
        """Save individual chapter script to file."""
        chapter = chapter_data['chapter']
        chapter_num = chapter['number']
        title = self.sanitize_filename(chapter['title'])
        
        filename = f"第{chapter_num}章_{title}.md"
        filepath = output_dir / filename
        
        # Create content with metadata
        content = f"""# 第{chapter_num}章: {chapter['title']}

生成日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

{script}
"""
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logging.info(f"Saved chapter script: {filepath}")
        return str(filepath)
    
    def create_output_directory(self, date: str = None) -> Path:
        """Create output directory for the date."""
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        base_path = Path(self.config.get('paths.output_base'))
        output_dir = base_path / date
        output_dir.mkdir(parents=True, exist_ok=True)
        
        return output_dir


class LineNotifier:
    """Send notifications via LINE Notify API."""
    
    def __init__(self, config: RadioGeneratorConfig):
        self.config = config
        self.token = os.getenv(self.config.get('line.token_env'))
    
    def send_notification(self, message: str) -> bool:
        """Send notification message via LINE."""
        if not self.token:
            logging.warning(f"LINE token not found in environment variable: {self.config.get('line.token_env')}")
            return False
        
        try:
            headers = {
                'Authorization': f'Bearer {self.token}',
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            
            data = {'message': message}
            
            response = requests.post(
                self.config.get('line.api_url'),
                headers=headers,
                data=data,
                timeout=10
            )
            
            if response.status_code == 200:
                logging.info("LINE notification sent successfully")
                return True
            else:
                logging.error(f"LINE notification failed: {response.status_code}")
                return False
        
        except Exception as e:
            logging.error(f"Failed to send LINE notification: {e}")
            return False


class RadioGenerator:
    """Main radio generation system."""
    
    def __init__(self, config_file: str = "radio_config.json"):
        self.config = RadioGeneratorConfig(config_file)
        self.setup_logging()
        
        self.chapter_extractor = ChapterExtractor(
            self.config.get('settings.chapter_marker')
        )
        self.script_generator = RadioScriptGenerator(self.config)
        self.file_manager = FileManager(self.config)
        self.line_notifier = LineNotifier(self.config)
    
    def setup_logging(self):
        """Setup logging configuration."""
        log_level = getattr(logging, self.config.get('settings.log_level', 'INFO'))
        
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('radio_generator.log', encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
    
    def process_report(self, date: str = None) -> Dict[str, any]:
        """
        Main processing function.
        
        Args:
            date: Date string (YYYY-MM-DD) for report, defaults to today
            
        Returns:
            Dictionary with processing results
        """
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        try:
            logging.info(f"Starting radio generation for date: {date}")
            
            # Step 1: Read research report
            logging.info("Reading research report...")
            research_report = self.file_manager.read_research_report(date)
            
            # Step 2: Extract chapters
            logging.info("Extracting chapters...")
            chapters = self.chapter_extractor.extract_chapters(research_report)
            logging.info(f"Found {len(chapters)} chapters")
            
            # Step 3: Create output directory
            output_dir = self.file_manager.create_output_directory(date)
            logging.info(f"Output directory: {output_dir}")
            
            # Step 4: Generate scripts for all chapters
            logging.info("Generating radio scripts...")
            scripts = self.script_generator.generate_all_scripts(chapters, research_report)
            
            # Step 5: Save all chapter scripts
            logging.info("Saving chapter scripts...")
            saved_files = []
            for script_data in scripts:
                filepath = self.file_manager.save_chapter_script(
                    script_data, script_data['script'], output_dir
                )
                saved_files.append(filepath)
            
            # Step 6: Send LINE notification
            success_message = f"""ラジオ原稿生成完了 📻

日付: {date}
章数: {len(chapters)}
出力先: {output_dir}
生成時刻: {datetime.now().strftime('%H:%M:%S')}

生成された章:
""" + "\n".join([f"• 第{ch['number']}章: {ch['title']}" for ch in chapters])
            
            self.line_notifier.send_notification(success_message)
            
            logging.info("Radio generation completed successfully!")
            
            return {
                'success': True,
                'date': date,
                'chapters_count': len(chapters),
                'output_dir': str(output_dir),
                'saved_files': saved_files,
                'chapters': chapters
            }
        
        except Exception as e:
            error_message = f"ラジオ原稿生成エラー ❌\n\n日付: {date}\nエラー: {str(e)}\n時刻: {datetime.now().strftime('%H:%M:%S')}"
            
            logging.error(f"Radio generation failed: {e}")
            self.line_notifier.send_notification(error_message)
            
            return {
                'success': False,
                'error': str(e),
                'date': date
            }


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='ラジオ原稿自動生成システム')
    parser.add_argument('--date', type=str, help='処理する日付 (YYYY-MM-DD)')
    parser.add_argument('--config', type=str, default='radio_config.json', 
                       help='設定ファイルのパス')
    
    args = parser.parse_args()
    
    generator = RadioGenerator(args.config)
    result = generator.process_report(args.date)
    
    if result['success']:
        print(f"✅ 処理完了: {result['chapters_count']}章を生成")
        print(f"📁 出力先: {result['output_dir']}")
    else:
        print(f"❌ 処理失敗: {result['error']}")
        exit(1)


if __name__ == "__main__":
    main()