#!/usr/bin/env python3
"""
章抽出テスト - 実際のレポートで何章抽出されるかチェック
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.config_loader import get_config
from radio_generator import RadioGeneratorConfig, ChapterExtractor

def test_real_report_extraction():
    """実際のレポートで章抽出テスト"""
    print("🔍 実際のレポートでの章抽出テスト")
    
    config = RadioGeneratorConfig()
    extractor = ChapterExtractor(config.get('settings.chapter_marker'))
    
    # 2025-09-12のレポートを読み込み
    report_path = "/Users/haruki/Library/Mobile Documents/iCloud~md~obsidian/Documents/I-think-therefore-I-am/artifact/research-report/2025-09-12.md"
    
    try:
        with open(report_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        chapters = extractor.extract_chapters(content)
        
        print(f"📊 抽出された章数: {len(chapters)}")
        print("📝 章一覧:")
        for chapter in chapters:
            print(f"  {chapter['number']}. {chapter['title']}")
        
        return len(chapters)
    
    except Exception as e:
        print(f"❌ エラー: {e}")
        return 0

if __name__ == "__main__":
    test_real_report_extraction()