#!/bin/bash

# auto-get-myinfo メイン実行スクリプト
# 環境変数に基づいて各コレクター、フォーマッター、出力処理を実行

# スクリプトディレクトリを取得
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR"
TOOLS_ROOT="$(dirname "$PROJECT_DIR")"

# 共通環境変数を読み込み（失敗時は終了）
if ! source "$TOOLS_ROOT/scripts/load-env.sh"; then
    echo "FATAL: Environment loading failed - aborting execution" >&2
    exit 1
fi

# ログ設定
LOG_FILE="$PROJECT_DIR/logs/auto-get-myinfo.log"
mkdir -p "$(dirname "$LOG_FILE")"

# ログ関数
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# エラーハンドリング
set -e
trap 'log "ERROR: Main script failed at line $LINENO"' ERR

# 実行開始ログ
log "=== Auto Get MyInfo System Started ==="

# 引数処理
TARGET_DATE="${1:-$(date -v-1d '+%Y-%m-%d')}"
FORCE_RUN="${2:-false}"

log "INFO: Target date: $TARGET_DATE"
log "INFO: Force run: $FORCE_RUN"

# Safari設定（常に有効、プログラムに組み込み）
SAFARI_ENABLED="true"
SAFARI_MIN_VISIT_COUNT="1"
EXCLUDE_PATTERNS="localhost,127.0.0.1,private browsing"

# Markdown設定（常に有効）
MARKDOWN_ENABLED="true"
MARKDOWN_TEMPLATE="({timestamp}){title},{url}, {visit_count}回"
MARKDOWN_HEADER="### 今日の閲覧履歴"

# Obsidian出力設定（常に有効）
OBSIDIAN_ENABLED="true"

# 一時ディレクトリ作成
TEMP_DIR="/tmp/auto-get-myinfo-$$"
mkdir -p "$TEMP_DIR"
trap 'rm -rf "$TEMP_DIR"' EXIT

log "INFO: Using temporary directory: $TEMP_DIR"

# データ収集フェーズ
log "INFO: Starting data collection phase"

# Safari履歴収集（常に有効）
if [ "$SAFARI_ENABLED" = "true" ]; then
    # Safari事前操作の実行
    log "INFO: Executing Safari pre-operation"
    if "$PROJECT_DIR/collectors/safari-preoperation.sh"; then
        log "INFO: Safari pre-operation completed successfully"
    else
        log "WARN: Safari pre-operation failed, but continuing with history collection"
    fi
    
    log "INFO: Collecting Safari history"
    SAFARI_DATA_FILE="$TEMP_DIR/safari_data.json"
    
    if "$PROJECT_DIR/collectors/safari.sh" > "$SAFARI_DATA_FILE"; then
        log "INFO: Safari history collection completed"
        
        # データが空でないかチェック
        if [ -s "$SAFARI_DATA_FILE" ]; then
            log "INFO: Safari data collected successfully"
        else
            log "WARN: No Safari data collected for $TARGET_DATE"
        fi
    else
        log "ERROR: Safari history collection failed"
        exit 1
    fi
fi

# データフォーマットフェーズ
log "INFO: Starting data formatting phase"

# Markdownフォーマット処理（常に有効）
if [ "$MARKDOWN_ENABLED" = "true" ]; then
    log "INFO: Formatting data to Markdown"
    MARKDOWN_FILE="$TEMP_DIR/formatted.md"
    
    if "$PROJECT_DIR/formatters/markdown.sh" "$SAFARI_DATA_FILE" > "$MARKDOWN_FILE"; then
        log "INFO: Markdown formatting completed"
    else
        log "ERROR: Markdown formatting failed"
        exit 1
    fi
fi

# データ出力フェーズ
log "INFO: Starting data output phase"

# Obsidian出力処理（常に有効）
if [ "$OBSIDIAN_ENABLED" = "true" ]; then
    log "INFO: Outputting to Obsidian"
    
    if "$PROJECT_DIR/outputs/obsidian.sh" "$TARGET_DATE" "$MARKDOWN_FILE"; then
        log "INFO: Obsidian output completed successfully"
    else
        log "ERROR: Obsidian output failed"
        exit 1
    fi
fi

# 実行完了ログ
log "INFO: All processing completed successfully"
log "=== Auto Get MyInfo System Finished ==="

# 成功終了
exit 0