# ラジオ原稿自動生成システム (Radio Script Auto-Generation System)

リサーチレポートの章構造に基づいてラジオトーク台本を自動生成し、各章ごとにファイル保存、LINE通知を行う完全自動ワークフローシステムです。

## 📋 システム概要

1. **入力**: 指定パスのリサーチレポート(.md)を読み込み
2. **解析**: `#automation/research-chapter`マーカー以降の章構造を抽出
3. **生成**: Azure OpenAI GPT-4を使って各章のラジオトーク台本を生成
4. **保存**: 章ごとにMarkdownファイルとして保存
5. **通知**: LINE Notifyで完了通知

## 🚀 セットアップ

### 1. 依存関係のインストール

```bash
pip install -r requirements_radio.txt
```

### 2. 環境変数の設定

`.env`ファイルを作成し、以下の環境変数を設定：

```env
# Azure OpenAI API設定
AZURE_OPENAI_API_KEY=your_azure_openai_api_key

# LINE Notify設定（オプション）
LINE_NOTIFY_TOKEN=your_line_notify_token
```

### 3. 設定ファイルの作成

```bash
cp radio_config.json.example radio_config.json
```

`radio_config.json`を編集して、以下の項目を環境に合わせて設定：

- `azure_openai.base_url`: Azure OpenAIリソースのURL
- `paths.research_report`: リサーチレポートファイルのパス
- `paths.prompt_template`: プロンプトテンプレートファイルのパス
- `paths.output_base`: 出力先ディレクトリのベースパス

## 📖 使用方法

### 基本実行

```bash
# 今日の日付のレポートを処理
python3 radio_generator.py

# または実行スクリプトを使用
./run_radio.sh
```

### 特定の日付のレポートを処理

```bash
python3 radio_generator.py --date 2025-09-07
```

### カスタム設定ファイルを使用

```bash
python3 radio_generator.py --config custom_config.json
```

## 📁 ファイル構造

### 入力ファイルの要件

リサーチレポートファイルは以下の形式で章構造を含む必要があります：

```markdown
# レポートタイトル

...レポート内容...

構成：
#automation/research-chapter
1. **人類の現在地と万博の示す未来像**（あなたが感じた「人類フェーズ」の分析）
2. **現実と統合する創造的自己理解**（哲学的・心理学的位置付け）
3. **人×システム協業の最前線**（新時代のライフハック術）
4. **小さな現実創造のための実装術**（具体的アクション提案）
5. **おすすめ作品・体験**（長期的視野での創造性拡張）
```

### 出力ファイル

生成されたラジオ台本は以下の形式で保存されます：

```
/output_base_path/
├── 2025-09-07/
│   ├── 第1章_人類の現在地と万博の示す未来像.md
│   ├── 第2章_現実と統合する創造的自己理解.md
│   ├── 第3章_人×システム協業の最前線.md
│   ├── 第4章_小さな現実創造のための実装術.md
│   └── 第5章_おすすめ作品・体験.md
```

## ⚙️ 設定項目

### Azure OpenAI設定
- `api_key_env`: API キーの環境変数名
- `base_url`: Azure OpenAI エンドポイントURL
- `model`: 使用するモデル名（例: gpt-4o）

### LINE Notify設定
- `token_env`: LINE Notify トークンの環境変数名
- `api_url`: LINE Notify API URL

### パス設定
- `research_report`: 入力レポートファイルのパス（{date}プレースホルダー使用可）
- `prompt_template`: プロンプトテンプレートファイルのパス
- `output_base`: 出力先ベースディレクトリ

### 動作設定
- `chapter_marker`: 章構造を示すマーカー
- `api_delay`: API呼び出し間隔（秒）
- `max_retries`: API失敗時の再試行回数
- `log_level`: ログレベル（DEBUG, INFO, WARNING, ERROR）

## 🔄 自動実行（cron設定例）

毎日朝9時に自動実行する場合：

```bash
# crontabを編集
crontab -e

# 以下を追加
0 9 * * * /path/to/tools/run_radio.sh
```

## 🛠️ AI生成の流れ

システムは**同一セッション履歴管理**で各章の台本を生成します：

1. **第1章**: プロンプトテンプレート + 全リサーチレポート
2. **第2章以降**: 「次の章」のメッセージのみ送信
3. 前章までの履歴を維持して一貫性のある会話を実現

## 📝 ログとエラーハンドリング

- ログファイル: `radio_generator.log`
- 主要なエラーハンドリング:
  - ファイル不存在
  - API通信エラー
  - 章構造抽出失敗
  - LINE通知失敗

## 🔧 トラブルシューティング

### よくある問題

1. **APIキーエラー**
   - 環境変数が正しく設定されているか確認
   - Azure OpenAIリソースのURLが正しいか確認

2. **ファイルが見つからない**
   - パス設定が正しいか確認
   - ファイルの存在と読み取り権限を確認

3. **章構造が抽出できない**
   - `#automation/research-chapter`マーカーが存在するか確認
   - 番号付きリストの形式が正しいか確認

4. **LINE通知が届かない**
   - LINE Notifyトークンが正しいか確認
   - ネットワーク接続を確認

## 📊 システム要件

- Python 3.7+
- インターネット接続（API呼び出しのため）
- Azure OpenAI API アクセス
- LINE Notify アクセス（通知機能使用時）

## 🔄 拡張機能

システムは以下の拡張に対応しています：

- 章数の可変対応
- カスタムプロンプトテンプレート
- 複数の通知方法
- スケジュール実行と手動実行の両対応
- ファイル形式の拡張

## 📞 サポート

問題が発生した場合は、以下を確認してください：

1. ログファイル (`radio_generator.log`) の内容
2. 設定ファイルの内容
3. 環境変数の設定
4. 入力ファイルの形式

---

**Generated with [Claude Code](https://claude.ai/code)**