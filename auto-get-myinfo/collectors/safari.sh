#!/bin/bash

# Safari履歴収集スクリプト
# macOS用Safari履歴を取得してJSON形式で出力

# スクリプトディレクトリを取得
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# 設定ファイル読み込み
CONFIG_FILE="$PROJECT_DIR/config/sources.yaml"

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

# Safari履歴を取得するSQLクエリ
# Safariのタイムスタンプは Mac絶対時間 (2001-01-01からの秒数)
# Unix時間に変換するため 978307200 を加算
SQL_QUERY="
SELECT 
  strftime('%H:%M', datetime(MIN(visit_time) + 978307200, 'unixepoch', 'localtime')) as first_visit,
  title,
  url,
  COUNT(*) as visit_count
FROM history_visits 
JOIN history_items ON history_visits.history_item = history_items.id
WHERE date(datetime(visit_time + 978307200, 'unixepoch', 'localtime')) = '$TARGET_DATE'
  AND title != ''
  AND title NOT LIKE '%localhost%'
  AND title NOT LIKE '%127.0.0.1%'
GROUP BY title, url
ORDER BY MIN(visit_time) ASC;
"

# SQLクエリ実行とJSON形式出力
sqlite3 "$SAFARI_HISTORY_DB" "$SQL_QUERY" | while IFS='|' read -r time title url count; do
    # エスケープ処理
    title=$(echo "$title" | sed 's/"/\\"/g')
    url=$(echo "$url" | sed 's/"/\\"/g')
    
    # JSON出力
    cat << EOF
{
  "timestamp": "$time",
  "title": "$title",
  "url": "$url", 
  "visit_count": $count,
  "source": "safari",
  "date": "$TARGET_DATE"
}
EOF
done

log "Safari history collection completed successfully"