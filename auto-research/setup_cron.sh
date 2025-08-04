#!/bin/bash

# 自動リサーチシステムのcron設定スクリプト（venv対応版）
# 毎朝5:30に実行するように設定

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/venv"

echo "Setting up cron job for auto research system..."
echo "Script directory: $SCRIPT_DIR"

# venvディレクトリの存在確認
if [ ! -d "$VENV_DIR" ]; then
    echo "Error: Virtual environment not found at $VENV_DIR"
    echo "Please run 'python3 -m venv venv' first to create the virtual environment"
    exit 1
fi

# venv内のpythonの存在確認
if [ ! -f "$VENV_DIR/bin/python" ]; then
    echo "Error: Python executable not found in virtual environment"
    echo "Please check your virtual environment setup"
    exit 1
fi

echo "Virtual environment found: $VENV_DIR"
echo "Python executable: $VENV_DIR/bin/python"

# ラッパースクリプトを使用したcrontabエントリを作成
CRON_ENTRY="30 5 * * * cd $SCRIPT_DIR && ./run_auto_research.sh >> auto_research_cron.log 2>&1"

# 既存のcrontabを取得し、新しいエントリを追加
(crontab -l 2>/dev/null; echo "$CRON_ENTRY") | crontab -

echo "Cron job added successfully!"
echo "The system will run daily at 5:30 AM using the virtual environment"
echo "Logs will be saved to: $SCRIPT_DIR/auto_research_cron.log"
echo ""
echo "To view current cron jobs: crontab -l"
echo "To remove the cron job: crontab -e (then delete the line)"