#!/usr/bin/env python3
"""
ラジオ原稿自動生成システム (Radio Script Auto-Generation System)

This system processes research reports and generates radio talk scripts 
for each chapter using Azure OpenAI API with conversation history management.
"""

import os
import re
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

# 共通ライブラリを追加
sys.path.insert(0, str(Path(__file__).parent.parent))
from shared.config_loader import get_config
from shared.api_clients.azure_openai_client import AzureOpenAIClient
from shared.api_clients.line_notify_client import LineNotifyClient
from shared.utils.file_utils import sanitize_filename, ensure_directory, format_date_for_path, get_file_with_date_placeholder


class RadioGeneratorConfig:
    """Configuration management for the radio generator - now using common config."""
    
    def __init__(self, config_file: str = None):
        """
        Initialize with common configuration system
        
        Args:
            config_file: Legacy parameter (ignored, kept for compatibility)
        """
        self.common_config = get_config()
        
    def get(self, key_path: str, default=None):
        """Get configuration value using dot notation."""
        # Map legacy keys to new common config keys
        key_mappings = {
            'azure_openai.api_key_env': 'AZURE_OPENAI_API_KEY',
            'azure_openai.base_url': 'AZURE_OPENAI_BASE_URL',
            'azure_openai.model': 'AZURE_OPENAI_DEPLOYMENT',
            'line.token_env': 'LINE_NOTIFY_TOKEN',
            'line.api_url': 'LINE_NOTIFY_API_URL',
            'paths.research_report': 'RESEARCH_REPORT_PATH',
            'paths.prompt_template': 'RADIO_PROMPT_TEMPLATE_PATH', 
            'paths.output_base': 'RADIO_OUTPUT_PATH',
            'settings.chapter_marker': 'CHAPTER_MARKER',
            'settings.api_delay': 'API_DELAY',
            'settings.max_retries': 'MAX_RETRIES',
            'settings.log_level': 'LOG_LEVEL'
        }
        
        if key_path in key_mappings:
            env_key = key_mappings[key_path]
            # 特別なフォーマット処理
            if key_path == 'paths.research_report':
                base_path = self.common_config.get(env_key)
                return f"{base_path}/{{date}}.md" if base_path else default
            else:
                return self.common_config.get(env_key, default)
        
        return default


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
        
        # Find the first substantial content block (stop at next major heading or empty line patterns)
        lines = after_marker.split('\n')
        chapter_section = []
        
        for i, line in enumerate(lines):
            # Stop at next major section or when we see repeated patterns
            if (i > 0 and line.strip() and 
                (line.startswith('##') or line.startswith('#') or 
                 (i > 20 and line.strip().startswith('0.')))):  # Stop if we see another "0." after some content
                break
            chapter_section.append(line)
            # Stop after finding a reasonable number of chapters (to avoid duplicates)
            if len([l for l in chapter_section if re.match(r'^\d+\.', l.strip())]) > 15:
                break
        
        chapter_text = '\n'.join(chapter_section)
        
        # Extract numbered chapters using regex
        # Pattern matches: 1. **Title** or 1. ****Title**** or 1. Simple Title
        chapter_pattern = r'(\d+)\.\s*(?:\*{2,4}([^*\n]+)\*{2,4}|([^\n]+))'
        raw_matches = re.findall(chapter_pattern, chapter_text)
        
        # Process matches (handle both bold and plain formats) and deduplicate
        matches = []
        seen_numbers = set()
        for match in raw_matches:
            number = match[0]
            title = match[1] if match[1] else match[2]  # Use bold title or plain title
            if title.strip() and number not in seen_numbers:  # Skip empty titles and duplicates
                matches.append((number, title.strip()))
                seen_numbers.add(number)
        
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
        self.client = AzureOpenAIClient()  # Use common client
        self.conversation_history = []
    
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
                user_message = f"{prompt_template}\n\nレポート:\n{research_report}\n\n最初の章から始めてください: {chapter['content']}"
                
                # Reset conversation and set system message
                self.client.reset_conversation()
                self.client.add_system_message("あなたは経験豊富なラジオ番組制作者です。レポートを基に魅力的なラジオトーク台本を章ごとに作成します。各章の内容を深く理解し、聞き手が興味を持つような構成で台本を作成してください。")
                
                script_content = self.client.continue_conversation(user_message)
            else:
                # Subsequent chapters: just say "次の章"
                script_content = self.client.continue_conversation("次の章をお願いします。")
            
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
        return sanitize_filename(filename)  # Use common utility
    
    def save_chapter_script(self, chapter_data: Dict, script: str, 
                          output_dir: Path) -> str:
        """Save individual chapter script to file."""
        chapter = chapter_data['chapter']
        chapter_num = chapter['number']
        title = self.sanitize_filename(chapter['title'])
        
        filename = f"第{chapter_num}章_{title}.md"
        filepath = output_dir / filename
        
        # Create content with metadata
        content = f"""{script}"""
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logging.info(f"Saved chapter script: {filepath}")
        return str(filepath)
    
    def create_output_directory(self, date: str = None) -> Path:
        """Create output directory for the date."""
        if date is None:
            date = format_date_for_path(datetime.now())
        
        base_path = Path(self.config.get('paths.output_base'))
        output_dir = base_path / date
        return ensure_directory(output_dir)  # Use common utility


class LineNotifier:
    """Send notifications via LINE Notify API - wrapper for common client."""
    
    def __init__(self, config: RadioGeneratorConfig):
        self.config = config
        self.client = LineNotifyClient()  # Use common client
    
    def send_notification(self, message: str) -> bool:
        """Send notification message via LINE."""
        return self.client.send_message(message)


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