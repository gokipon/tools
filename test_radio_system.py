#!/usr/bin/env python3
"""
ラジオ原稿自動生成システムのテストスクリプト

このスクリプトはAPIを呼び出さずにシステムの基本機能をテストします。
"""

import os
import tempfile
from pathlib import Path
from radio_generator import (
    RadioGeneratorConfig, 
    ChapterExtractor, 
    FileManager
)


def test_chapter_extraction():
    """章構造抽出機能のテスト"""
    print("🧪 章構造抽出テスト...")
    
    sample_content = """
# テストレポート

これはテストレポートです。

## 構成：
#automation/research-chapter
1. **人類の現在地と万博の示す未来像**（あなたが感じた「人類フェーズ」の分析）
2. **現実と統合する創造的自己理解**（哲学的・心理学的位置付け）
3. **人×システム協業の最前線**（新時代のライフハック術）

## 詳細内容
...
"""
    
    extractor = ChapterExtractor()
    chapters = extractor.extract_chapters(sample_content)
    
    assert len(chapters) == 3, f"期待: 3章, 実際: {len(chapters)}章"
    assert chapters[0]['number'] == 1, "第1章の番号が正しくない"
    assert chapters[0]['title'] == "人類の現在地と万博の示す未来像", "第1章のタイトルが正しくない"
    
    print("✅ 章構造抽出テスト完了")
    return chapters


def test_config_loading():
    """設定ファイル読み込みテスト"""
    print("🧪 設定ファイル読み込みテスト...")
    
    # 一時的な設定ファイルを作成
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write('{"test": {"value": "success"}}')
        temp_config = f.name
    
    try:
        config = RadioGeneratorConfig(temp_config)
        assert config.get('test.value') == 'success', "設定値の読み込みが失敗"
        print("✅ 設定ファイル読み込みテスト完了")
    finally:
        os.unlink(temp_config)


def test_file_operations():
    """ファイル操作テスト"""
    print("🧪 ファイル操作テスト...")
    
    config = RadioGeneratorConfig()
    file_manager = FileManager(config)
    
    # ファイル名サニタイズテスト
    test_filename = "テスト/タイトル:特殊文字"
    sanitized = file_manager.sanitize_filename(test_filename)
    assert '/' not in sanitized, "スラッシュが除去されていない"
    assert ':' not in sanitized, "コロンが除去されていない"
    
    print(f"  元ファイル名: {test_filename}")
    print(f"  サニタイズ後: {sanitized}")
    
    # 出力ディレクトリ作成テスト（一時ディレクトリを使用）
    with tempfile.TemporaryDirectory() as temp_dir:
        # 設定を一時的に変更
        original_base = config.config['paths']['output_base']
        config.config['paths']['output_base'] = temp_dir
        
        output_dir = file_manager.create_output_directory("2025-09-07")
        assert output_dir.exists(), "出力ディレクトリが作成されていない"
        
        # 設定を元に戻す
        config.config['paths']['output_base'] = original_base
    
    print("✅ ファイル操作テスト完了")


def test_full_system_flow():
    """システム全体のフロー（API呼び出し除く）テスト"""
    print("🧪 システム全体フローテスト...")
    
    # テストデータの準備
    sample_report = """
# 今日のリサーチレポート

これは今日のリサーチレポートです。

## 構成：
#automation/research-chapter
1. **AIと人間の協業の現在地**（技術発展の現状分析）
2. **未来予測と戦略的思考**（長期的視野での考察）
3. **実装のためのアクションプラン**（具体的な行動指針）

## 詳細内容
各章の詳細な内容がここに続きます...
"""
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # テスト用の設定を作成
        test_config = {
            "azure_openai": {
                "api_key_env": "AZURE_OPENAI_API_KEY",
                "base_url": "https://test.openai.azure.com/openai/v1/",
                "model": "gpt-4o"
            },
            "paths": {
                "research_report": f"{temp_dir}/{{date}}.md",
                "output_base": temp_dir
            },
            "settings": {
                "chapter_marker": "#automation/research-chapter",
                "log_level": "INFO"
            }
        }
        
        # 設定ファイルを作成
        config_path = os.path.join(temp_dir, "test_config.json")
        import json
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(test_config, f, ensure_ascii=False, indent=2)
        
        # テストレポートファイルを作成
        report_path = os.path.join(temp_dir, "2025-09-07.md")
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(sample_report)
        
        # システムの初期化とテスト
        config = RadioGeneratorConfig(config_path)
        
        # 章抽出テスト
        extractor = ChapterExtractor(config.get('settings.chapter_marker'))
        chapters = extractor.extract_chapters(sample_report)
        assert len(chapters) == 3, f"期待: 3章, 実際: {len(chapters)}章"
        
        # ファイル読み込みテスト
        file_manager = FileManager(config)
        read_content = file_manager.read_research_report("2025-09-07")
        assert sample_report in read_content, "レポート内容の読み込みが失敗"
        
        # 出力ディレクトリ作成テスト
        output_dir = file_manager.create_output_directory("2025-09-07")
        assert output_dir.exists(), "出力ディレクトリの作成が失敗"
        
    print("✅ システム全体フローテスト完了")


def main():
    """メインテスト関数"""
    print("🚀 ラジオ原稿自動生成システム テスト開始\n")
    
    try:
        test_config_loading()
        print()
        
        test_chapter_extraction()
        print()
        
        test_file_operations()
        print()
        
        test_full_system_flow()
        print()
        
        print("🎉 全テスト完了！システムは正常に動作します。")
        print("\n次のステップ:")
        print("1. 環境変数を設定してください (AZURE_OPENAI_API_KEY, LINE_NOTIFY_TOKEN)")
        print("2. radio_config.jsonを環境に合わせて設定してください")
        print("3. プロンプトテンプレートファイルを準備してください")
        print("4. python3 radio_generator.py を実行してください")
        
    except Exception as e:
        print(f"❌ テスト失敗: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    main()