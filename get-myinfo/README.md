# auto-get-myinfo システム

パーソナル情報自動収集システム - Safari履歴を自動的に収集してObsidian日記に統合します。

## 🎯 概要

auto-get-myinfoは、macOS上でSafariの閲覧履歴を自動的に収集し、Obsidianの日記ファイル（Markdown形式）に整理して追記するシステムです。毎日決まった時刻に実行され、前日の閲覧履歴を自動で記録します。

## 🏗️ システム構成

```
auto-get-myinfo/
├── collectors/          # データ収集モジュール
│   └── safari.sh       # Safari履歴取得
├── formatters/         # データフォーマット変換
│   └── markdown.sh     # Markdown形式
├── outputs/            # 出力処理
│   └── obsidian.sh     # Obsidian日記出力
├── config/             # 設定ファイル
│   └── sources.yaml    # システム設定
├── logs/               # ログファイル（自動生成）
├── main.sh             # メイン実行スクリプト
└── README.md           # このファイル
```

## 📋 機能

- ✅ Safari履歴の自動収集
- ✅ Markdown形式でのフォーマット
- ✅ Obsidian日記ファイルへの自動追記
- ✅ 毎日の自動実行（launchd）
- ✅ 重複訪問の集約処理
- ✅ エラーハンドリングとログ記録


## 🚀 セットアップ

### 前提条件

- macOS
- Safari使用
- Obsidian使用
- フルディスクアクセス権限

### 1. ファイル配置

```bash
# このリポジトリをクローン or ダウンロード
git clone <repository_url>
cd tools/auto-get-myinfo
```

### 2. 権限設定

```bash
# 実行権限を付与
chmod +x main.sh
chmod +x collectors/safari.sh
chmod +x collectors/safari-preoperation.sh
chmod +x formatters/markdown.sh
chmod +x outputs/obsidian.sh
```

### 4. フルディスクアクセス権限の付与

1. システム環境設定 → セキュリティとプライバシー → プライバシー
2. フルディスクアクセスを選択
3. ターミナル.appを追加して有効化

### 5. 手動テスト

```bash
# 手動で実行してテスト　前日の履歴を処理（デフォルト）
./main.sh

# 特定の日付を指定して実行
./main.sh 2025-08-04
```

## 🔧 使用方法

### 手動実行

```bash

./main.sh

# 特定の日付を指定
./main.sh 2025-08-04

# 強制実行フラグ付き
./main.sh 2025-08-04 true
```



## 📄 出力例

Obsidianの日記ファイル（例：`2025/08/2025-08-04.md`）に以下の形式で追記されます：

```markdown
### 今日の閲覧履歴
(09:15)Personal Knowledge Management, 3回
(10:30)Obsidian Documentation, 2回
(11:45)Safari History Analysis, 1回
```

## ⚙️ 設定

`config/sources.yaml`で様々な設定を調整できます：

- **collectors**: データ収集の有効/無効
- **formatters**: 出力フォーマットの選択
- **outputs**: 出力先の設定
- **logging**: ログレベルとファイル設定

## 🛠️ トラブルシューティング

### よくある問題

1. **Safari履歴にアクセスできない**
   - フルディスクアクセス権限が必要です
   - ターミナル.appに権限を付与してください

2. **Obsidianファイルが作成されない**
   - `config/sources.yaml`のパス設定を確認
   - ディレクトリの書き込み権限を確認

3. **launchdが動作しない**
   - plistファイルのパス設定を確認
   - `launchctl load`が正常に実行されたか確認

### ログの確認

```bash
# エラーの詳細確認
grep ERROR logs/auto-get-myinfo.log

# 実行履歴の確認
grep "System Started" logs/auto-get-myinfo.log
```
