#!/usr/bin/env python3
"""基本機能テストスクリプト"""

import sys
import os
import logging

def test_imports():
    """モジュールインポートテスト"""
    print("=== モジュールインポートテスト ===")
    
    try:
        from web_automation import WebAutomation
        print("✓ WebAutomation インポート成功")
    except Exception as e:
        print(f"✗ WebAutomation インポート失敗: {e}")
        return False
    
    try:
        from web_automation.config.settings import Settings, get_settings
        print("✓ Settings インポート成功")
    except Exception as e:
        print(f"✗ Settings インポート失敗: {e}")
        return False
    
    try:
        from web_automation.core.browser_manager import BrowserManager
        print("✓ BrowserManager インポート成功")
    except Exception as e:
        print(f"✗ BrowserManager インポート失敗: {e}")
        return False
    
    try:
        from web_automation.core.prompt_builder import PromptBuilder
        print("✓ PromptBuilder インポート成功")
    except Exception as e:
        print(f"✗ PromptBuilder インポート失敗: {e}")
        return False
    
    return True


def test_settings():
    """設定機能テスト"""
    print("\n=== 設定機能テスト ===")
    
    try:
        from web_automation.config.settings import get_settings
        
        settings = get_settings()
        
        # デフォルト設定確認
        port = settings.get('chrome.remote_debugging_port')
        print(f"✓ デフォルトポート取得: {port}")
        
        # カスタム設定
        settings.set('test.value', 'test_data')
        test_value = settings.get('test.value')
        print(f"✓ カスタム設定: {test_value}")
        
        # パス生成
        template_path = settings.get_obsidian_template_path()
        print(f"✓ テンプレートパス: {template_path}")
        
        return True
        
    except Exception as e:
        print(f"✗ 設定機能テスト失敗: {e}")
        return False


def test_prompt_builder():
    """プロンプト構築機能テスト"""
    print("\n=== プロンプト構築テスト ===")
    
    try:
        from web_automation.core.prompt_builder import PromptBuilder
        
        builder = PromptBuilder()
        
        # テストファイル作成
        test_template = "/tmp/test_template.md"
        test_diary = "/tmp/test_diary.md"
        
        with open(test_template, 'w', encoding='utf-8') as f:
            f.write("# テンプレート\n\nこれはテストテンプレートです。")
        
        with open(test_diary, 'w', encoding='utf-8') as f:
            f.write("# テスト日記\n\n今日は良い一日でした。")
        
        # プロンプト構築テスト
        prompt = builder.build_prompt(test_template, test_diary)
        print(f"✓ プロンプト構築成功（長さ: {len(prompt)}文字）")
        
        # パス検証テスト
        validation = builder.validate_paths(test_template, test_diary)
        print(f"✓ パス検証: {validation}")
        
        # クリーンアップ
        os.remove(test_template)
        os.remove(test_diary)
        
        return True
        
    except Exception as e:
        print(f"✗ プロンプト構築テスト失敗: {e}")
        return False


def test_service_factory():
    """サービスファクトリテスト"""
    print("\n=== サービスファクトリテスト ===")
    
    try:
        from web_automation.services.base_service import ServiceFactory
        from web_automation.core.browser_manager import BrowserManager
        
        # ダミーのブラウザマネージャー
        browser_manager = BrowserManager()
        factory = ServiceFactory()
        
        # サービス名リスト
        services = ['perplexity', 'gmail', 'github', 'generic']
        
        for service_name in services:
            try:
                service = factory.get_service(service_name, browser_manager)
                print(f"✓ {service_name}サービス取得成功: {service.__class__.__name__}")
            except Exception as e:
                print(f"✗ {service_name}サービス取得失敗: {e}")
                return False
        
        return True
        
    except Exception as e:
        print(f"✗ サービスファクトリテスト失敗: {e}")
        return False


def test_error_handler():
    """エラーハンドラーテスト"""
    print("\n=== エラーハンドラーテスト ===")
    
    try:
        from web_automation.core.error_handler import ErrorHandler
        
        handler = ErrorHandler()
        
        # 正常処理のテスト
        def success_operation():
            return "成功"
        
        result = handler.retry_operation(success_operation, max_retries=1)
        print(f"✓ 正常処理テスト: {result}")
        
        # エラー文脈作成テスト
        context = handler.create_error_context("テスト操作", test_param="テスト値")
        print(f"✓ エラー文脈作成: {context['operation']}")
        
        return True
        
    except Exception as e:
        print(f"✗ エラーハンドラーテスト失敗: {e}")
        return False


def main():
    """メインテスト関数"""
    print("汎用Web自動化ライブラリ - 基本機能テスト\n")
    
    tests = [
        ("モジュールインポート", test_imports),
        ("設定機能", test_settings),
        ("プロンプト構築", test_prompt_builder),
        ("サービスファクトリ", test_service_factory),
        ("エラーハンドラー", test_error_handler),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
                print(f"✓ {test_name}テスト: 成功\n")
            else:
                print(f"✗ {test_name}テスト: 失敗\n")
        except Exception as e:
            print(f"✗ {test_name}テスト: 例外発生 - {e}\n")
    
    print(f"=== テスト結果 ===")
    print(f"成功: {passed}/{total}")
    print(f"失敗: {total - passed}/{total}")
    
    if passed == total:
        print("すべてのテストが成功しました！")
        return True
    else:
        print("一部のテストが失敗しました。")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)