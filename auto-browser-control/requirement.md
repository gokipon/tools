# 汎用Web自動化ライブラリ 要件定義書

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

#### F003: サービス別操作定義
- **機能**: 各Webサービス専用の操作クラス
- **詳細**: Perplexity、Gmail、GitHub等のサービス固有操作を抽象化
- **入力**: サービス名、操作パラメータ
- **出力**: 操作結果

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
│   └── error_handler.py      # エラーハンドリング
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
│   └── settings.py           # 基本設定（Pythonファイル）
└── main.py                   # メインAPI
```

### 使用例（理想形）

#### パターン1: サービス専用操作
```python
from web_automation import WebAutomation

automation = WebAutomation(port=9222)

with automation.connect() as browser:
    # Perplexity操作
    perplexity = automation.service('perplexity')
    result = perplexity.ask_question("AIの最新動向について教えて")
    
    # Gmail操作  
    gmail = automation.service('gmail')
    emails = gmail.get_unread_emails()
    
    # GitHub操作
    github = automation.service('github')
    repos = github.get_my_repositories()
```

#### パターン2: 汎用操作
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
2. **BaseService**: サービス抽象化基底クラス
3. **基本操作**: navigate, click, input, wait
4. **エラーハンドリング**: 基本的な例外処理

### Phase 2: サービス対応 (重要)
1. **PerplexityService**: 質問・回答取得
2. **GenericService**: 汎用操作のラッパー

### Phase 3: 高度機能 (任意)  
1. **GmailService**: メール操作
2. **GitHubService**: リポジトリ操作

---

## 🎯 成果物

### 最終成果物
- **メインライブラリ**: `web_automation/` パッケージ
- **使用例**: 1つの実践的サンプル

### 品質基準
- **動作確認**: 主要機能の手動テスト
- **コード品質**: 読みやすく保守しやすいコード

---

## ✅ 受け入れ条件

1. ✅ 検証済み手法での確実なブラウザ接続
2. ✅ サービス固有操作の抽象化
3. ✅ 汎用操作との使い分け可能
4. ✅ 新サービス追加の容易性
5. ✅ 適切なエラーハンドリング
6. ✅ 保守性の高いコード構造