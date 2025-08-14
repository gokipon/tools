#!/bin/bash

# Markdown形式フォーマッター
# JSON形式の履歴データをMarkdown形式に変換

# スクリプトディレクトリを取得
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"


# -------ログ---------
# ログ設定
LOG_FILE="$PROJECT_DIR/logs/markdown-formatter.log"

# ログ関数
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

# ------エラーハンドリング---------
set -e
trap 'log "ERROR: Markdown formatter failed at line $LINENO"' ERR

log "Markdown formatting started"

# 引数チェック
if [ $# -eq 0 ]; then
    log "ERROR: No input provided"
    echo "Usage: $0 [JSON_DATA_FILE]" >&2
    exit 1
fi

INPUT_FILE="$1"
if [ ! -f "$INPUT_FILE" ]; then
    log "ERROR: Input file not found: $INPUT_FILE"
    echo "ERROR: Input file not found: $INPUT_FILE" >&2
    exit 1
fi


# ------Markdownヘッダー出力---------
echo "### 今日の閲覧履歴"

# JSONデータを処理してMarkdown形式で出力
jq -r '"(" + .timestamp + ")" + "[" +.title + "]" +"(" + .url + "), " + (.visit_count | tostring) + "回"' "$INPUT_FILE" 2>/dev/null || {
    log "WARN: jq parsing failed"
}

log "Markdown formatting completed successfully"