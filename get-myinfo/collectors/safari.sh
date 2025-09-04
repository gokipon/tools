#!/bin/bash

# Safari履歴収集スクリプト
# macOS用Safari履歴を取得してJSON形式で出力

# スクリプトディレクトリを取得
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
TOOLS_ROOT="$(dirname "$PROJECT_DIR")"

# Safari設定（プログラムに組み込み、main.shから環境変数継承）
MIN_VISIT_COUNT="${SAFARI_MIN_VISIT_COUNT:-1}"
EXCLUDE_PATTERNS="${EXCLUDE_PATTERNS:-localhost,127.0.0.1,private browsing}"

# Safari履歴DBのパス
SAFARI_HISTORY_DB="$HOME/Library/Safari/History.db"

# ログ設定
LOG_FILE="$PROJECT_DIR/logs/safari-collector.log"

# ログ関数
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

# エラーハンドリング
set -e
trap 'log "ERROR: Script failed at line $LINENO"' ERR

log "Safari history collection started"

# Safari履歴DBの存在確認
if [ ! -f "$SAFARI_HISTORY_DB" ]; then
    log "ERROR: Safari history database not found at $SAFARI_HISTORY_DB"
    echo "ERROR: Safari history database not found" >&2
    exit 1
fi

# フルディスクアクセス権限の確認
if ! sqlite3 "$SAFARI_HISTORY_DB" "SELECT 1 LIMIT 1" >/dev/null 2>&1; then
    log "ERROR: Cannot access Safari history database. Full Disk Access permission required."
    echo "ERROR: Cannot access Safari history database. Full Disk Access permission required." >&2
    exit 1
fi

# 前日の日付を取得
TARGET_DATE=$(date -v-1d '+%Y-%m-%d')
log "Collecting Safari history for date: $TARGET_DATE"

# JSON文字列エスケープ関数
escape_json_string() {
    local input="$1"
    # 制御文字と特殊文字をエスケープ
    printf '%s\n' "$input" | \
    sed 's/\\/\\\\/g' | \
    sed 's/"/\\"/g' | \
    sed 's/	/\\t/g' | \
    sed 's/$/\\n/g' | tr -d '\n' | \
    sed 's/\\n$//' | \
    sed 's/\x08/\\b/g' | \
    sed 's/\x0C/\\f/g' | \
    sed 's/\x0D/\\r/g'
}

# JSON検証関数
validate_json() {
    local json_string="$1"
    echo "$json_string" | jq empty 2>/dev/null
}

# Safari履歴を取得するSQLクエリ
# Safariのタイムスタンプは Mac絶対時間 (2001-01-01からの秒数)  
# Unix時間に変換するため 978307200 を加算
SQL_QUERY="
SELECT 
  strftime('%H:%M', datetime(MIN(visit_time) + 978307200, 'unixepoch', 'localtime')) as first_visit,
  COALESCE(title, '') as title,
  url,
  COUNT(*) as visit_count
FROM history_visits 
JOIN history_items ON history_visits.history_item = history_items.id
WHERE date(datetime(visit_time + 978307200, 'unixepoch', 'localtime')) = '$TARGET_DATE'
  AND url NOT LIKE '%localhost%'
  AND url NOT LIKE '%127.0.0.1%'
GROUP BY title, url
ORDER BY MIN(visit_time) ASC;
"

# SQLクエリ実行とJSON形式出力（Unit Separator文字を使用）
sqlite3 -separator $'\x1F' "$SAFARI_HISTORY_DB" "$SQL_QUERY" | while IFS=$'\x1F' read -r time title url count; do
    
    # visit_countが数値であることを確認
    if ! [[ "$count" =~ ^[0-9]+$ ]]; then
        log "WARN: Invalid visit count '$count' for URL '$url', setting to 1"
        count=1
    fi
    
    # JSON文字列エスケープ
    escaped_title=$(escape_json_string "$title")
    escaped_url=$(escape_json_string "$url")
    
    # JSON生成
    json_record=$(cat << EOF
{
  "timestamp": "$time",
  "title": "$escaped_title",
  "url": "$escaped_url",
  "visit_count": $count,
  "source": "safari",
  "date": "$TARGET_DATE"
}
EOF
)
    
    # JSON検証
    if validate_json "$json_record"; then
        echo "$json_record"
    else
        log "WARN: Skipping malformed JSON record for URL: $escaped_url"
        log "DEBUG: Malformed JSON: $json_record"
    fi
done

log "Safari history collection completed successfully"