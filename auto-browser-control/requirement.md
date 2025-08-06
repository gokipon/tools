#### F003: サービス別操作定義
- **機能**: 各Webサービス専用の操作クラス
- **詳細**: Perplexity、Gmail、GitHub等のサービス固有操作を抽象化
- **入力**: サービス名、操作パラメータ
- **出力**: 操作結果# 汎用Web自動化ライブラリ 要件定義書

## 🎯 プロジェクト概要

### 目的
様々なWebサービス（Perplexity、Gmail、GitHub等）を統一的に自動操作できる、汎用性と保守性を重視したPythonライブラリの開発

### 成功した検証手法
```bash
# 1. Chrome Remote Debuggingモードで起動
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --remote-debugging-port=9222 \
  --user-data-dir=/tmp/chrome-selenium-debug

# 2. 手動ログイン後、Seleniumでアタッチ
options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")

#　以降のselenium実行には手動ログインの必要なし。

```

---

## 📋 機能要件

### 🔧 コア機能

#### F001: Chrome接続管理
- **機能**: Remote Debugging接続の自動化
- **詳細**: Chrome起動 → 接続 → 切断まで一元管理
- **入力**: ポート番号、プロファイルパス
- **出力**: WebDriverインスタンス

#### F002: エラーハンドリング
- **機能**: 接続失敗・タイムアウトの自動復旧
- **詳細**: 再試行ロジック、フォールバック処理
- **入力**: エラー情報
- **出力**: 復旧済みWebDriver

#### F004: プロンプトテンプレート機能
- **機能**: Obsidianファイルを読み込んでプロンプト生成
- **詳細**: デイリーリサーチ.md + 前日の日記ファイルを組み合わせ
- **入力**: テンプレートパス、日記パス（日付自動計算）
- **出力**: 結合されたプロンプト文字列

#### F005: スケジュール実行機能  
- **機能**: 毎朝定時でのcron自動実行対応
- **詳細**: CLI引数での実行、結果の保存機能
- **入力**: なし（設定ファイルから取得）
- **出力**: 実行結果ファイル

---

## 🛠 非機能要件

### N001: 保守性
- **コード構造**: クラスベース設計
- **ログ出力**: Python標準loggingでシンプルに

### N002: 使いやすさ
- **API設計**: 直感的なメソッド名
- **エラーメッセージ**: 分かりやすい説明
- **型安全性**: Type Hints完備

### N003: 信頼性
- **自動復旧**: 3回まで再試行
- **タイムアウト**: 操作ごとに適切な待機時間
- **リソース管理**: finally句での確実なクリーンアップ

---

## 🏗 アーキテクチャ設計

### クラス構成
```
WebAutomation/
├── core/
│   ├── browser_manager.py    # ブラウザ接続管理
│   ├── error_handler.py      # エラーハンドリング
│   └── prompt_builder.py     # プロンプト構築
├── services/
│   ├── base_service.py       # サービス基底クラス
│   ├── perplexity.py         # Perplexity専用操作
│   ├── gmail.py              # Gmail専用操作
│   ├── github.py             # GitHub専用操作
│   └── generic.py            # 汎用操作
├── utils/
│   ├── element_helper.py     # 要素操作ヘルパー
│   ├── wait_helper.py        # 待機処理
│   └── screenshot.py         # スクリーンショット
├── config/
│   └── settings.py           # 基本設定（パス情報含む）
├── scripts/
│   └── daily_research.py     # cron実行用スクリプト
└── main.py                   # メインAPI
```

### 使用例（理想形）

#### パターン1: デイリーリサーチ（メイン用途）
```python
from web_automation import WebAutomation
from datetime import datetime, timedelta

automation = WebAutomation(port=9222)

# 前日の日記パスを自動生成
yesterday = datetime.now() - timedelta(days=1)
diary_path = f"/Users/haruki/Library/Mobile Documents/iCloud~md~obsidian/Documents/I-think-therefore-I-am/diary/{yesterday.year}/{yesterday.month:02d}/{yesterday.strftime('%Y-%m-%d')}.md"

with automation.connect() as browser:
    # プロンプト自動構築
    prompt = automation.build_prompt(
        template_path="/Users/haruki/Library/Mobile Documents/iCloud~md~obsidian/Documents/I-think-therefore-I-am/knowledge/llm-usecase/デイリーリサーチ.md",
        diary_path=diary_path
    )
    
    # Perplexity で質問実行
    perplexity = automation.service('perplexity')
    result = perplexity.ask_question(prompt)
    
    # 結果を保存（オプション）
    automation.save_result(result, f"research_{datetime.now().strftime('%Y-%m-%d')}.md")
```

#### パターン2: CLI実行（cron用）
```bash
# cron設定例
30 5 * * * cd /path/to/project && python scripts/daily_research.py

# 手動実行
python scripts/daily_research.py --date 2024-01-01  # 特定日指定
python scripts/daily_research.py                    # 今日実行（前日の日記使用）
```

#### パターン3: 汎用操作
```python
# 汎用操作での柔軟な処理
with automation.connect() as browser:
    browser.navigate("https://example.com")
    browser.input_text("#search", "検索クエリ")
    browser.click_button("[data-testid='submit']")
    results = browser.wait_for_elements(".result")
```
```

---

## 📝 実装優先度

### Phase 1: 基礎機能 (必須)
1. **BrowserManager**: 接続・切断の基本機能
2. **PerplexityService**: 質問・回答取得
3. **PromptBuilder**: Obsidianファイル読み込み・結合
4. **基本操作**: navigate, click, input, wait
5. **エラーハンドリング**: 基本的な例外処理

### Phase 2: 自動化対応 (重要)  
1. **daily_research.py**: cron実行用スクリプト
2. **結果保存機能**: 実行結果のファイル保存
3. **日付計算**: 前日日記の自動パス生成
4. **CLI引数処理**: 日付指定実行

### Phase 3: 拡張機能 (任意)
1. **GmailService**: メール操作
2. **GitHubService**: リポジトリ操作
3. **GenericService**: 汎用操作のラッパー

---

## 🎯 成果物

### 最終成果物
- **メインライブラリ**: `web_automation/` パッケージ
- **自動実行スクリプト**: `scripts/daily_research.py`
- **cron設定例**: README記載
- **使用例**: 1つの実践的サンプル

### 品質基準
- **動作確認**: 主要機能の手動テスト
- **コード品質**: 読みやすく保守しやすいコード

---

## ✅ 受け入れ条件

1. ✅ 検証済み手法での確実なブラウザ接続
2. ✅ Obsidianファイル読み込み・プロンプト構築
3. ✅ 前日日記の自動パス生成
4. ✅ cron等での定時自動実行
5. ✅ Perplexity質問・回答取得
6. ✅ 実行結果の保存機能
7. ✅ 新サービス追加の容易性
8. ✅ 適切なエラーハンドリング
9. ✅ 保守性の高いコード構造