#!/bin/bash

# Obsidian出力ハンドラー
# フォーマットされたMarkdownをObsidianの日記ファイルに追記

# スクリプトディレクトリを取得
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
TOOLS_ROOT="$(dirname "$PROJECT_DIR")"

# ログ設定
LOG_FILE="$PROJECT_DIR/logs/obsidian-output.log"

# ログ関数
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

# エラーハンドリング
set -e
trap 'log "ERROR: Obsidian output failed at line $LINENO"' ERR

log "Obsidian output started"

# 引数チェック
if [ $# -lt 2 ]; then
    echo "Usage: $0 <TARGET_DATE> <MARKDOWN_CONTENT_FILE>" >&2
    exit 1
fi

TARGET_DATE="$1"
MARKDOWN_FILE="$2"

if [ ! -f "$MARKDOWN_FILE" ]; then
    log "ERROR: Markdown content file not found: $MARKDOWN_FILE"
    echo "ERROR: Markdown content file not found: $MARKDOWN_FILE" >&2
    exit 1
fi

# 環境変数からObsidianパスを取得（load-env.shで検証済み）
OBSIDIAN_BASE_PATH="$USER_INFO_PATH"

# 日付から年月を取得
YEAR=$(echo "$TARGET_DATE" | cut -d'-' -f1)
MONTH=$(echo "$TARGET_DATE" | cut -d'-' -f2)

# 出力ディレクトリを作成
OUTPUT_DIR="$OBSIDIAN_BASE_PATH/$YEAR/$MONTH"
if [ ! -d "$OUTPUT_DIR" ]; then
    log "INFO: Creating output directory: $OUTPUT_DIR"
    mkdir -p "$OUTPUT_DIR" || {
        log "ERROR: Failed to create output directory: $OUTPUT_DIR"
        echo "ERROR: Failed to create output directory: $OUTPUT_DIR" >&2
        exit 1
    }
fi

# 出力ファイルパス
OUTPUT_FILE="$OUTPUT_DIR/$TARGET_DATE.md"
log "INFO: Output file path: $OUTPUT_FILE"

# Markdownコンテンツの存在確認
CONTENT_SIZE=$(wc -l < "$MARKDOWN_FILE")
if [ "$CONTENT_SIZE" -le 1 ]; then
    log "INFO: No content to append (empty or header only)"
    echo "INFO: No browsing history found for $TARGET_DATE"
    exit 0
fi

# 既存ファイルがある場合は末尾に改行を追加してから追記
if [ -f "$OUTPUT_FILE" ]; then
    log "INFO: Appending to existing file: $OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"
else
    log "INFO: Creating new file: $OUTPUT_FILE"
fi

# Markdownコンテンツを追記
cat "$MARKDOWN_FILE" >> "$OUTPUT_FILE"

# 追加した行数をログ出力
ADDED_LINES=$(wc -l < "$MARKDOWN_FILE")
log "INFO: Successfully appended $ADDED_LINES lines to $OUTPUT_FILE"

echo "Successfully updated diary file: $OUTPUT_FILE"