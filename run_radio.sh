#!/bin/bash
# ラジオ原稿自動生成システム実行スクリプト

# スクリプトのディレクトリに移動
cd "$(dirname "$0")"

# 環境変数を読み込み（.envファイルがある場合）
if [ -f .env ]; then
    export $(cat .env | grep -v '#' | xargs)
fi

# Pythonでラジオ生成を実行
python3 radio_generator.py "$@"