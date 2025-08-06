# 汎用Web自動化ライブラリ

Chrome Remote Debuggingを使用してWebサービス（Perplexity、Gmail、GitHub等）を自動操作するPythonライブラリです。

## 🚀 特徴

- **統一的なAPI**: 様々なWebサービスを同じインターフェースで操作
- **Chrome Remote Debugging**: 手動ログイン状態を維持した自動化
- **Obsidian連携**: テンプレートファイルと日記ファイルを組み合わせたプロンプト生成
- **cron対応**: 定時自動実行をサポート
- **エラーハンドリング**: 自動復旧機能付き

## 📦 インストール

```bash
# リポジトリをクローン
git clone <このリポジトリのURL>
cd auto-browser-control

# 依存関係をインストール
pip install -r requirements.txt
```

## 🔧 事前準備

### 1. Chrome Remote Debuggingモードで起動

```bash
# macOS
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --remote-debugging-port=9222 \
  --user-data-dir=/tmp/chrome-selenium-debug

# Linux
google-chrome \
  --remote-debugging-port=9222 \
  --user-data-dir=/tmp/chrome-selenium-debug
```

### 2. 手動ログイン

Chrome Remote Debuggingモードで起動後、使用したいWebサービス（Perplexity等）に手動でログインしてください。

## 💡 使用方法

### 基本的な使用例

```python
from web_automation import WebAutomation
from datetime import datetime, timedelta

# WebAutomationインスタンス作成
automation = WebAutomation(port=9222)

# 前日の日記パス自動生成
yesterday = datetime.now() - timedelta(days=1)
diary_path = f"/path/to/obsidian/diary/{yesterday.year}/{yesterday.month:02d}/{yesterday.strftime('%Y-%m-%d')}.md"

with automation.connect() as browser:
    # プロンプト自動構築
    prompt = automation.build_prompt(
        template_path="/path/to/template.md",
        diary_path=diary_path
    )
    
    # Perplexity で質問実行
    perplexity = automation.service('perplexity')
    result = perplexity.ask_question(prompt)
    
    # 結果を保存
    automation.save_result(result, f"research_{datetime.now().strftime('%Y-%m-%d')}.md")
```

### CLI実行（デイリーリサーチ）

```bash
# 基本実行（前日の日記を使用）
python web_automation/scripts/daily_research.py

# 特定日付を指定
python web_automation/scripts/daily_research.py --date 2024-01-01

# 設定確認（Dry Run）
python web_automation/scripts/daily_research.py --dry-run

# カスタムポート使用
python web_automation/scripts/daily_research.py --port 9223

# 詳細ログ
python web_automation/scripts/daily_research.py --log-level DEBUG
```

### cron設定例

```bash
# crontabを編集
crontab -e

# 毎朝5:30に自動実行
30 5 * * * cd /path/to/auto-browser-control && python web_automation/scripts/daily_research.py >> daily_research.log 2>&1
```

## 🔧 設定

### 環境変数の設定

マシン固有の情報や機密情報は環境変数で設定します。

#### 必須環境変数

```bash
# Obsidianのベースディレクトリパス（必須）
export OBSIDIAN_BASE_PATH="/Users/username/Documents/ObsidianVault"
```

#### オプション環境変数

```bash
# Chromeデバッグポート（デフォルト: 9222）
export CHROME_DEBUG_PORT=9222

# Chromeユーザーデータディレクトリ（デフォルト: /tmp/chrome-selenium-debug）
export CHROME_USER_DATA_DIR="/tmp/chrome-selenium-debug"

# テンプレートファイル相対パス（デフォルト: knowledge/llm-usecase/デイリーリサーチ.md）
export TEMPLATE_FILE="templates/daily_research.md"

# 日記ディレクトリ相対パス（デフォルト: diary）
export DIARY_BASE="diary"

# 出力ディレクトリ（デフォルト: ./output）
export OUTPUT_DIR="./output"
```

#### .envファイルの使用

プロジェクトルートに`.env`ファイルを作成することで、環境変数を管理できます：

```bash
# .envファイルをコピーして編集
cp .env.example .env
# エディタで必要な値を設定
```

`.env`ファイルの例：
```bash
# 必須設定
OBSIDIAN_BASE_PATH=/Users/yourname/Documents/ObsidianVault

# オプション設定（必要に応じてコメントアウト）
# TEMPLATE_FILE=knowledge/llm-usecase/デイリーリサーチ.md
# DIARY_BASE=diary
# OUTPUT_DIR=./output
# CHROME_DEBUG_PORT=9222
# CHROME_USER_DATA_DIR=/tmp/chrome-selenium-debug
```

### アプリケーション設定ファイル（config.json）

アプリケーションの動作設定は`config.json`で管理します：

```json
{
  "chrome": {
    "remote_debugging_port": 9222,
    "startup_timeout": 10
  },
  "automation": {
    "default_timeout": 30,
    "retry_count": 3,
    "retry_delay": 2.0
  },
  "logging": {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "file": "web_automation.log"
  }
}
```

## 🌐 サポートサービス

| サービス | 機能 | ステータス |
|---------|------|-----------|
| Perplexity | 質問・回答取得 | ✅ 実装済み |
| Gmail | メール送信・受信 | ✅ 実装済み |
| GitHub | Issue作成・リポジトリ情報取得 | ✅ 実装済み |
| Generic | 汎用操作 | ✅ 実装済み |

## 📁 プロジェクト構造

```
web_automation/
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
│   └── settings.py           # 設定管理
├── scripts/
│   └── daily_research.py     # デイリーリサーチスクリプト
└── main.py                   # メインAPI
```

## 🔍 トラブルシューティング

### Chrome接続エラー

1. Chrome Remote Debuggingモードで起動されているか確認
2. ポート番号（デフォルト9222）が利用可能か確認
3. 他のChromeプロセスが動作していないか確認

### 要素が見つからないエラー

1. サイトの仕様変更によりセレクタが変更された可能性
2. ページの読み込みが完了していない可能性
3. ログイン状態が切れている可能性

### ファイルパスエラー

1. Obsidianのベースパスが正しく設定されているか確認
2. テンプレートファイルと日記ファイルが存在するか確認
3. 出力ディレクトリの書き込み権限を確認

## 📄 ライセンス

このプロジェクトはMITライセンスの下で公開されています。

## 🤝 コントリビューション

1. このリポジトリをフォーク
2. 機能ブランチを作成 (`git checkout -b feature/amazing-feature`)
3. コミット (`git commit -m 'Add some amazing feature'`)
4. ブランチにプッシュ (`git push origin feature/amazing-feature`)
5. プルリクエストを作成

## 📞 サポート

問題や質問がある場合は、Issueを作成してください。