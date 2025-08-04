#!/bin/bash

# 自動リサーチシステムのcron設定スクリプト
# 毎朝5:30に実行するように設定

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_PATH=$(which python3)

echo "Setting up cron job for auto research system..."
echo "Script directory: $SCRIPT_DIR"
echo "Python path: $PYTHON_PATH"

# crontabエントリを作成
CRON_ENTRY="30 5 * * * cd $SCRIPT_DIR && $PYTHON_PATH auto_research.py >> auto_research_cron.log 2>&1"

# 既存のcrontabを取得し、新しいエントリを追加
(crontab -l 2>/dev/null; echo "$CRON_ENTRY") | crontab -

echo "Cron job added successfully!"
echo "The system will run daily at 5:30 AM"
echo "Logs will be saved to: $SCRIPT_DIR/auto_research_cron.log"
echo ""
echo "To view current cron jobs: crontab -l"
echo "To remove the cron job: crontab -e (then delete the line)"