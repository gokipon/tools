# auto-get-myinfo システム開発要件書

## 🎯 プロジェクト概要

### システム名
**auto-get-myinfo** - パーソナル情報自動収集システム

### 目的
ユーザーの日常的なデジタル活動（ブラウザ履歴、カレンダー、写真など）を自動で収集し、Obsidianの日記ファイルに統合して、無意識領域の情報を可視化する。

### 背景
- AIを活用するためには個人情報のインプットが重要
- 意識的な情報入力だけでなく、無意識に生成される情報の価値が高い
- 手動での情報収集は継続性に課題がある

## 🏗️ システム設計

### アーキテクチャ構成

```
tools/auto-get-myinfo/
├── collectors/          # 各情報源の取得モジュール
│   ├── safari.sh       # Safari履歴取得
│   ├── chrome.sh       # Chrome履歴取得 (将来)
│   ├── calendar.sh     # カレンダー予定取得 (将来)
│   └── photos.sh       # 写真EXIF取得 (将来)
├── formatters/         # 出力フォーマット変換
│   ├── markdown.sh     # Markdown形式
│   └── json.sh         # JSON形式 (将来)
├── outputs/            # 出力先管理
│   ├── obsidian.sh     # Obsidian日記
│   └── csv.sh          # CSV出力 (将来)
├── config/             # 設定ファイル
│   └── sources.yaml    # 有効/無効、実行時刻等
├── logs/               # ログファイル
└── main.sh             # 統合実行スクリプト
```

### 実行フロー
1. **main.sh** が設定ファイル（sources.yaml）を読み込み
2. 有効化された **collectors** を順次実行してデータ取得
3. **formatters** で指定形式にデータ整形
4. **outputs** で各出力先に配信
5. 実行ログを記録

## 📋 機能要件

### Phase 1: Safari履歴取得機能（最優先）

#### 基本仕様
- **データソース**: Safari履歴DB (`~/Library/Safari/History.db`)
- **実行タイミング**: 毎日 0:30 自動実行
- **取得対象**:  前日　00:00-23:59 の全閲覧履歴
- **出力先**: Obsidianの日記ファイル

#### データ取得仕様
```sql
-- 基本的なSQLクエリ例
SELECT 
  strftime('%H:%M', datetime(MIN(visit_time) + 978307200, 'unixepoch', 'localtime')) as first_visit,
  title,
  COUNT(*) as visit_count
FROM history_visits 
WHERE date(datetime(visit_time + 978307200, 'unixepoch', 'localtime')) = date('now', 'localtime', '-1 day')
  AND title != ''
GROUP BY title
ORDER BY MIN(visit_time) DESC;
```

#### 出力フォーマット
```markdown
### 今日の閲覧履歴
(11:25)Personal Knowledge Management Automation, 3回
(10:50)Readwise - Google Search, 1回
(09:43)Readwise を中心とした情報収集フローを構築する, 2回
```

#### ファイル出力仕様
- **出力先**: `/Users/haruki/Library/Mobile Documents/iCloud~md~obsidian/Documents/I-think-therefore-I-am/diary/2025/MM/YYYY-MM-DD.md`
- **追記位置**: ファイル末尾
- **存在しない場合**: 新規ファイル作成
- **フォルダが存在しない場合**: 自動作成

### Phase 2以降の拡張予定

#### 対応予定の情報源
- Chrome履歴
- Googleカレンダー予定
- 写真のEXIF情報
- PayPay利用履歴
- 音楽再生履歴
- アプリ利用履歴

## ⚙️ 技術要件

### 動作環境
- **OS**: macOS (現在の対象)
- **必要権限**: フルディスクアクセス権限
- **依存ソフト**: sqlite3, yq (YAML処理)

### 自動実行設定
- **実行方式**: launchd (macOSの標準的なスケジューラ)
- **設定ファイル**: `~/Library/LaunchAgents/com.user.auto-get-myinfo.plist`

### 設定ファイル仕様 (config/sources.yaml)
```yaml
collectors:
  safari:
    enabled: true
    schedule: "0 30 0 * * *"  # 毎日0:30実行
    min_visit_count: 1        # 最小訪問回数
    exclude_sites: []         # 除外サイト（現在は空）
  chrome:
    enabled: false
    schedule: "0 30 0 * * *"

formatters:
  markdown:
    enabled: true
  json:
    enabled: false

outputs:
  obsidian:
    enabled: true
    base_path: "diary"
    path_format: "{YYYY}/{MM}/{YYYY-MM-DD}.md"
  csv:
    enabled: false
    path: "exports/history_{YYYY-MM-DD}.csv"

logging:
  enabled: true
  level: "INFO"
  path: "logs/auto-get-myinfo.log"
```

## 🛡️ セキュリティ・プライバシー要件

### データ保護
- 取得したデータはローカルのみに保存
- 外部送信は行わない

### 権限管理
- 必要最小限の権限のみ要求
- Safari履歴へのアクセスにはフルディスクアクセス権限が必要

## 🚀 開発・テスト要件

### 開発手順
1. **Phase 1**: Safari履歴取得機能の実装
2. **手動テスト**: 開発者環境での動作確認
3. **自動実行テスト**: launchd設定での定期実行確認
4. **Phase 2以降**: 他の情報源への拡張

### テストケース
- [ ] Safari履歴の正常取得
- [ ] 日記ファイルの新規作成
- [ ] 既存日記ファイルへの追記
- [ ] 権限不足時のエラーハンドリング
- [ ] 空データ時の処理
- [ ] 重複データの集約処理

### エラーハンドリング
- Safari履歴DBへのアクセス失敗
- 出力先ディレクトリの作成失敗
- 権限不足エラー
- 設定ファイルの読み込みエラー

## 📦 成果物

### 最終的な成果物
1. **実行可能スクリプト一式**
2. **設定ファイル** (sources.yaml)
3. **launchd設定ファイル** (.plist)
4. **README.md** (セットアップ手順書)
5. **テスト用スクリプト**

### ドキュメント
- セットアップガイド
- 使用方法説明書
- トラブルシューティングガイド
- 拡張開発ガイド

## 🎯 受け入れ基準

### Phase 1完了条件
- [ ] Safari履歴が毎日自動で取得される
- [ ] Obsidianの日記ファイルに正しい形式で追記される
- [ ] 重複訪問が回数で集約される
- [ ] エラー時にログが記録される
- [ ] 手動での実行も可能
- [ ] 設定ファイルでの有効/無効切り替えが機能する

### 品質基準
- 連続7日間の自動実行が成功する
- メモリリーク等のリソース問題がない
- 実行時間が30秒以内に完了する

## 💡 実装上の注意点

### Safari履歴DB について
- Safariが起動中はDBがロックされる可能性
- 時刻変換が必要（Unix timestamp + 978307200秒のオフセット）
- フルディスクアクセス権限が必須

### macOS固有の考慮事項
- launchdの設定方法
- ~/Library/へのアクセス権限
- システムアップデート時の動作継続性

### 将来の拡張性
- 新しい情報源の追加が容易な設計
- 出力フォーマットの変更に柔軟に対応
- 他のOS（Windows, Linux）への移植可能性を考慮