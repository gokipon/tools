#!/usr/bin/env python3
"""使用例スクリプト"""

from web_automation import WebAutomation
from web_automation.config.settings import setup_logging, get_settings
from datetime import datetime, timedelta
import logging

# ログ設定
setup_logging()
logger = logging.getLogger(__name__)


def example_daily_research():
    """デイリーリサーチの使用例"""
    print("=== デイリーリサーチの例 ===")
    
    # WebAutomationインスタンス作成
    automation = WebAutomation(port=9222)
    
    # 前日の日記パスを自動生成（例）
    yesterday = datetime.now() - timedelta(days=1)
    diary_path = f"/Users/haruki/Library/Mobile Documents/iCloud~md~obsidian/Documents/I-think-therefore-I-am/diary/{yesterday.year}/{yesterday.month:02d}/{yesterday.strftime('%Y-%m-%d')}.md"
    template_path = "/Users/haruki/Library/Mobile Documents/iCloud~md~obsidian/Documents/I-think-therefore-I-am/knowledge/llm-usecase/デイリーリサーチ.md"
    
    try:
        with automation.connect() as browser:
            # プロンプト自動構築
            prompt = automation.build_prompt(template_path, diary_path)
            print(f"生成されたプロンプトの長さ: {len(prompt)}文字")
            
            # Perplexity で質問実行
            perplexity = automation.service('perplexity')
            result = perplexity.ask_question(prompt)
            
            # 結果を保存
            output_file = f"research_{datetime.now().strftime('%Y-%m-%d_%H%M%S')}.md"
            automation.save_result(result, output_file)
            
            print(f"結果を保存しました: {output_file}")
            
    except Exception as e:
        logger.error(f"デイリーリサーチエラー: {e}")


def example_github_operations():
    """GitHub操作の使用例"""
    print("=== GitHub操作の例 ===")
    
    automation = WebAutomation(port=9222)
    
    try:
        with automation.connect() as browser:
            github = automation.service('github')
            
            # リポジトリ情報取得
            repo_info = github.get_repository_info("https://github.com/microsoft/vscode")
            print(f"リポジトリ情報: {repo_info}")
            
            # リポジトリ検索
            search_results = github.search_repositories("python selenium", limit=3)
            print(f"検索結果: {len(search_results)}件")
            for repo in search_results[:2]:
                print(f"- {repo.get('name')}: {repo.get('description')}")
                
    except Exception as e:
        logger.error(f"GitHub操作エラー: {e}")


def example_generic_operations():
    """汎用操作の使用例"""
    print("=== 汎用操作の例 ===")
    
    automation = WebAutomation(port=9222)
    
    try:
        with automation.connect() as browser:
            generic = automation.service('generic')
            
            # Googleに移動
            generic.navigate("https://www.google.com")
            
            # 検索ボックスに入力
            success = generic.input_text('textarea[name="q"], input[name="q"]', "Python selenium automation")
            if success:
                print("検索クエリ入力成功")
            
            # 検索ボタンクリック
            click_success = generic.click_button('input[type="submit"], button[type="submit"]')
            if click_success:
                print("検索実行成功")
            
            # 結果を少し待機
            import time
            time.sleep(3)
            
            # 検索結果のタイトルを取得
            titles = generic.wait_for_elements('h3')
            print(f"検索結果: {len(titles)}件のタイトルを発見")
            
            # スクリーンショット撮影
            screenshot_path = generic.take_screenshot("google_search_example.png")
            if screenshot_path:
                print(f"スクリーンショット保存: {screenshot_path}")
                
    except Exception as e:
        logger.error(f"汎用操作エラー: {e}")


def example_settings_usage():
    """設定機能の使用例"""
    print("=== 設定機能の例 ===")
    
    settings = get_settings()
    
    # 設定値を取得
    print(f"Chrome デバッグポート: {settings.get('chrome.remote_debugging_port')}")
    print(f"Obsidian ベースパス: {settings.get('paths.obsidian_base')}")
    print(f"出力ディレクトリ: {settings.get_output_dir()}")
    
    # カスタム設定
    settings.set('custom.example_setting', 'example_value')
    print(f"カスタム設定: {settings.get('custom.example_setting')}")


def main():
    """メイン処理"""
    print("Web自動化ライブラリ使用例\n")
    
    try:
        # 設定機能の例
        example_settings_usage()
        print()
        
        # Chrome Remote Debuggingの確認
        print("注意: 以下の例を実行する前に、Chrome Remote Debuggingモードで起動してください。")
        print("コマンド例:")
        print("/Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome \\")
        print("  --remote-debugging-port=9222 \\")
        print("  --user-data-dir=/tmp/chrome-selenium-debug")
        print()
        
        response = input("Chrome Remote Debuggingモードで起動済みですか？ (y/N): ")
        
        if response.lower() in ['y', 'yes']:
            # 汎用操作の例（比較的安全）
            example_generic_operations()
            print()
            
            # GitHub操作の例
            example_github_operations()
            print()
            
            # デイリーリサーチは実際のファイルが必要なのでコメントアウト
            # example_daily_research()
            
            print("すべての例が完了しました。")
        else:
            print("Chrome Remote Debuggingモードで起動後、再度実行してください。")
            
    except KeyboardInterrupt:
        print("\n処理が中断されました。")
    except Exception as e:
        logger.error(f"例外エラー: {e}")
        print(f"エラーが発生しました: {e}")


if __name__ == "__main__":
    main()