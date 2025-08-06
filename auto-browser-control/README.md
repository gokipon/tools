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

### 設定ファイル（config.json）

```json
{
  "chrome": {
    "remote_debugging_port": 9222,
    "user_data_dir": "/tmp/chrome-selenium-debug"
  },
  "paths": {
    "obsidian_base": "/Users/username/obsidian/vault",
    "template_file": "templates/daily_research.md",
    "diary_base": "diary",
    "output_dir": "output"
  },
  "automation": {
    "default_timeout": 30,
    "retry_count": 3
  }
}
```

### 環境変数

```bash
export CHROME_DEBUG_PORT=9222
export OBSIDIAN_BASE_PATH="/Users/username/obsidian/vault"
export OUTPUT_DIR="./output"
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