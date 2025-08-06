#!/bin/bash

# Markdown形式フォーマッター
# JSON形式の履歴データをMarkdown形式に変換

# スクリプトディレクトリを取得
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# ログ設定
LOG_FILE="$PROJECT_DIR/logs/markdown-formatter.log"

# ログ関数
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

# エラーハンドリング
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

# Markdownヘッダー出力
echo "### 今日の閲覧履歴"

# JSONデータを処理してMarkdown形式で出力
# jqが利用可能な場合はjqを使用、そうでなければ手動パース
if command -v jq >/dev/null 2>&1; then
    # jqを使用したパース
    jq -r '"(" + .timestamp + ")" + .title + ", " + (.visit_count | tostring) + "回"' "$INPUT_FILE" 2>/dev/null || {
        log "WARN: jq parsing failed, falling back to manual parsing"
        # 手動パース
        while IFS= read -r line; do
            if echo "$line" | grep -q '"timestamp"'; then
                timestamp=$(echo "$line" | sed -n 's/.*"timestamp": "\([^"]*\)".*/\1/p')
                title=$(echo "$line" | sed -n 's/.*"title": "\([^"]*\)".*/\1/p')
                visit_count=$(echo "$line" | sed -n 's/.*"visit_count": \([0-9]*\).*/\1/p')
                
                if [ -n "$timestamp" ] && [ -n "$title" ] && [ -n "$visit_count" ]; then
                    echo "($timestamp)$title, ${visit_count}回"
                fi
            fi
        done < "$INPUT_FILE"
    }
else
    # 手動パース（jqが利用できない場合）
    log "INFO: jq not available, using manual parsing"
    while IFS= read -r line; do
        if echo "$line" | grep -q '"timestamp"'; then
            timestamp=$(echo "$line" | sed -n 's/.*"timestamp": "\([^"]*\)".*/\1/p')
            title=$(echo "$line" | sed -n 's/.*"title": "\([^"]*\)".*/\1/p')
            visit_count=$(echo "$line" | sed -n 's/.*"visit_count": \([0-9]*\).*/\1/p')
            
            if [ -n "$timestamp" ] && [ -n "$title" ] && [ -n "$visit_count" ]; then
                echo "($timestamp)$title, ${visit_count}回"
            fi
        fi
    done < "$INPUT_FILE"
fi

log "Markdown formatting completed successfully"