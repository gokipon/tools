#!/bin/bash

# 自動リサーチシステム実行ラッパースクリプト
# venv環境でのcron実行用

# スクリプトディレクトリを取得
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/venv"

# ログファイルにタイムスタンプを出力
echo "=== Auto Research System Started at $(date) ===" 

# venvディレクトリの存在確認
if [ ! -d "$VENV_DIR" ]; then
    echo "Error: Virtual environment not found at $VENV_DIR"
    exit 1
fi

# venv内のpythonの存在確認
if [ ! -f "$VENV_DIR/bin/python" ]; then
    echo "Error: Python executable not found in virtual environment"
    exit 1
fi

# スクリプトディレクトリに移動
cd "$SCRIPT_DIR" || {
    echo "Error: Cannot change directory to $SCRIPT_DIR"
    exit 1
}

# 仮想環境をアクティベート
echo "Activating virtual environment..."
source "$VENV_DIR/bin/activate" || {
    echo "Error: Failed to activate virtual environment"
    exit 1
}

# 必要なパッケージがインストールされているかチェック
python -c "import requests; print('Dependencies OK')" || {
    echo "Error: Required packages not found. Please run 'pip install -r requirements.txt'"
    deactivate
    exit 1
}

# メインスクリプト実行
echo "Starting auto research system..."
python auto_research.py

# 実行結果を記録
RESULT=$?
if [ $RESULT -eq 0 ]; then
    echo "Auto research system completed successfully at $(date)"
else
    echo "Auto research system failed with exit code $RESULT at $(date)"
fi

# 仮想環境を非アクティベート
deactivate

echo "=== Auto Research System Finished at $(date) ==="
echo ""

exit $RESULT