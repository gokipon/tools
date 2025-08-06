#!/bin/bash

# auto-get-myinfo メイン実行スクリプト
# 設定ファイルに基づいて各コレクター、フォーマッター、出力処理を実行

# スクリプトディレクトリを取得
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR"

# 設定ファイル
CONFIG_FILE="$PROJECT_DIR/config/sources.yaml"

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

# 設定ファイルの存在確認
if [ ! -f "$CONFIG_FILE" ]; then
    log "ERROR: Configuration file not found: $CONFIG_FILE"
    exit 1
fi

# 一時ディレクトリ作成
TEMP_DIR="/tmp/auto-get-myinfo-$$"
mkdir -p "$TEMP_DIR"
trap 'rm -rf "$TEMP_DIR"' EXIT

log "INFO: Using temporary directory: $TEMP_DIR"

# データ収集フェーズ
log "INFO: Starting data collection phase"

# Safari履歴収集（設定ファイルでenabledの場合のみ）
# 簡易的な設定確認（実際の実装ではyamlパーサーを使用）
if grep -q "safari:" "$CONFIG_FILE" && grep -A 2 "safari:" "$CONFIG_FILE" | grep -q "enabled: true"; then
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
else
    log "INFO: Safari collector is disabled"
    # 空のファイルを作成
    touch "$TEMP_DIR/safari_data.json"
fi

# データフォーマットフェーズ
log "INFO: Starting data formatting phase"

# Markdownフォーマット処理（設定でenabledの場合のみ）
if grep -q "markdown:" "$CONFIG_FILE" && grep -A 2 "markdown:" "$CONFIG_FILE" | grep -q "enabled: true"; then
    log "INFO: Formatting data to Markdown"
    MARKDOWN_FILE="$TEMP_DIR/formatted.md"
    
    if "$PROJECT_DIR/formatters/markdown.sh" "$SAFARI_DATA_FILE" > "$MARKDOWN_FILE"; then
        log "INFO: Markdown formatting completed"
    else
        log "ERROR: Markdown formatting failed"
        exit 1
    fi
else
    log "INFO: Markdown formatter is disabled"
    exit 0
fi

# データ出力フェーズ
log "INFO: Starting data output phase"

# Obsidian出力処理（設定でenabledの場合のみ）
if grep -q "obsidian:" "$CONFIG_FILE" && grep -A 2 "obsidian:" "$CONFIG_FILE" | grep -q "enabled: true"; then
    log "INFO: Outputting to Obsidian"
    
    if "$PROJECT_DIR/outputs/obsidian.sh" "$TARGET_DATE" "$MARKDOWN_FILE"; then
        log "INFO: Obsidian output completed successfully"
    else
        log "ERROR: Obsidian output failed"
        exit 1
    fi
else
    log "INFO: Obsidian output is disabled"
fi

# 実行完了ログ
log "INFO: All processing completed successfully"
log "=== Auto Get MyInfo System Finished ==="

# 成功終了
exit 0