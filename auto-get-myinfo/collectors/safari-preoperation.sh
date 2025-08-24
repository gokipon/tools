#!/bin/bash

# Safari事前操作スクリプト
# Safari履歴収集前に意図的なブラウジング活動を実行
# AppleScriptによるSafari自動制御

# スクリプトディレクトリを取得
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# ログ設定
LOG_FILE="$PROJECT_DIR/logs/safari-preoperation.log"
mkdir -p "$(dirname "$LOG_FILE")"

# ログ関数
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# エラーハンドリング
set -e
trap 'log "ERROR: Safari pre-operation failed at line $LINENO"' ERR

# Safari事前操作の設定
TARGET_URL="https://zenn.dev/"
WAIT_DURATION=10

log "=== Safari Pre-operation Started ==="
log "INFO: Target URL: $TARGET_URL"
log "INFO: Wait duration: ${WAIT_DURATION} seconds"

# macOSプラットフォーム確認
if [[ "$(uname)" != "Darwin" ]]; then
    log "ERROR: This script requires macOS"
    echo "ERROR: Safari pre-operation requires macOS" >&2
    exit 1
fi

# AppleScriptでSafari操作を実行
log "INFO: Executing Safari automation via AppleScript"

osascript << EOF
try
    -- Safari起動確認・起動
    tell application "Safari"
        -- Safari起動（既に起動していても問題なし）
        activate
        
        -- 少し待機してSafariが完全に起動するまで待つ
        delay 2
        
        -- 新規タブでターゲットURLを開く
        tell window 1
            make new tab with properties {URL:"$TARGET_URL"}
        end tell
        
        -- ページ読み込み完了まで待機
        delay 3
        
    end tell
    
    return "SUCCESS: Safari opened $TARGET_URL"
    
on error errorMessage number errorNumber
    return "ERROR: " & errorMessage & " (Error " & errorNumber & ")"
end try
EOF

# AppleScriptの実行結果を取得
APPLESCRIPT_RESULT=$?

if [ $APPLESCRIPT_RESULT -eq 0 ]; then
    log "INFO: Safari successfully opened $TARGET_URL"
    log "INFO: Waiting $WAIT_DURATION seconds for history DB reflection..."
    
    # 履歴DBへの反映を待機
    sleep $WAIT_DURATION
    
    # Safari終了
    log "INFO: Closing Safari application"
    osascript << EOF
try
    tell application "Safari"
        quit
    end tell
    
    -- Safariが完全に終了するまで待機
    delay 2
    
    return "SUCCESS: Safari closed"
    
on error errorMessage number errorNumber
    return "ERROR: Failed to close Safari - " & errorMessage
end try
EOF
    
    CLOSE_RESULT=$?
    if [ $CLOSE_RESULT -eq 0 ]; then
        log "INFO: Safari closed successfully"
    else
        log "WARN: Safari close operation may have failed, but continuing"
    fi
    
    log "INFO: Safari pre-operation completed successfully"
    
else
    log "ERROR: AppleScript execution failed"
    echo "ERROR: Failed to execute Safari automation" >&2
    exit 1
fi

log "=== Safari Pre-operation Finished ==="
exit 0