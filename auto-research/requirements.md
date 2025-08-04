# 自動リサーチシステム要件定義書  
（Obsidian日記→APIリサーチ→.md化→iCloud同期）

## 1. システム全体概要

### 1.1 目的
- ユーザーの日記（Obsidian vault, iCloud同期）から注目ワード・問いを抽出し、
- Perplexity API([Sonar Deep Research](https://docs.perplexity.ai/getting-started/models/models/sonar-deep-research)を利用)による専門的リサーチを自動実行、
- 結果をMarkdown（.md）形式で所定フォルダに保存、
- そのままスマホを含めた全端末で簡単に閲覧できる知的自動化サイクルを構築する。

### 1.2 特徴
- 毎朝、最新の“本質に刺さる良質な情報”のみが新着Noteとして見られる
- 日記から「自分独自のテーマ・問い」を毎回動的取得→マンネリ化やノイズ疲れを防ぐ
- システム思考／根本理解志向／長期的視点に最適化

## 2. 機能仕様

### 2.1 入力仕様
- Obsidian vault内の日記（例：`diary/YYYY/MM/DD.md`）をiCloud経由で参照可能な状態に
- 前日と前々日の2日分.mdファイルを取得しプロンプトの一部分として活用する。
    ※　前日の日記の文字数が3000以上だった場合、前々日の日記は必要としない。

### 2.2 プロンプト生成
- 専用のプロンプトテンプレートファイル（`/Users/haruki/Library/Mobile Documents/iCloud~md~obsidian/Documents/I-think-therefore-I-am/knowledge/インプット体系/情報取得の仕組み.md`）から指示を読み込み
- 日記の内容と組み合わせて、Perplexity API用の自然文プロンプトを自動生成

### 2.3 リサーチAPI実行（Macサーバー上）
- 毎朝定時（例: 5:30）にcron等で自動発火
- Pythonスクリプト（推奨）で
    - プロンプト→API（Sonar deep research）POST
    - レスポンス受信（詳細なレポート取得）
- APIキー等の認証情報は安全管理（.envファイルに保存）

### 2.4 アウトプット（Obsidian .md形式ファイル自動生成）
- 保存フォルダ：`'/Users/haruki/Library/Mobile Documents/iCloud~md~obsidian/Documents/I-think-therefore-I-am/artifact/research-report/2025-08-04.md'`配下（Obsidian vault内）
- ファイル命名：【YYYY/MM/DD.md】例：`2025-08-04.md`
- Markdown内に
    - APIのレスポンスを貼り付ける。

### 2.5 iCloud同期・スマホ閲覧
- 保存先がvault以下/icloud同期済みなら、スマホのObsidianで即座に新着確認可能

## 3. 運用仕様

- 日々の日記執筆がそのまま「問い供給源」となる
- 前日・前々日の2日間の気づきや問いが翌朝の“知的リサーチ”テーマになるサイクル
- 使いながらプロンプト・ファイルレイアウトなど随時改善可能

## 4. 推奨技術・セキュリティ

- メイン言語：**Python3系**（AppleScript/Automatorより管理・メンテしやすい）
- モジュール例：`os`, `glob`, `re`, `requests`, `markdown` etc.
- サーバー自体は常時稼働不要、定時バッチのみ動作、落ちても再実行容易
- APIキー等は**秘密ストレージ**で管理
- 外部サービスperplexityのAPI仕様に依存しない（他のサービスに変更可能な）保守性の高いコードにする。

## 5. 適用範囲・発展性

- まずは「artifact/research-report/」フォルダへの自動リサーチNote保存からスタート
- 慣れたら「問いメタデータ」等の連携、さらなるキーワード抽出精度改善やline, gmail連携など拡張可能
- 個人の“知的リフレクションサイクル”を最小手間で動かせる仕組み

## 6. 参考・備考

- 「プロンプトはユーザー自身で調整」仕様なのでシステム側は柔軟な入力を許容
- Obsidian側のワークフローやNote設計（タグ、テンプレ等）も随時チューニング推奨
- 不具合や失敗時はエラーログのみ保存、動作通知（メール/SMS/Obsidian内pop等）も必要なら追加
