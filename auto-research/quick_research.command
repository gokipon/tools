#!/bin/bash

# Quick Research Script - デイリーリサーチをPerplexityで実行するためのクイックコマンド

# 設定
OBSIDIAN_DIARY_PATH="/Users/haruki/Library/Mobile Documents/iCloud~md~obsidian/Documents/I-think-therefore-I-am/diary"
RESEARCH_TEMPLATE_PATH="/Users/haruki/Library/Mobile Documents/iCloud~md~obsidian/Documents/I-think-therefore-I-am/knowledge/自動実行用/デイリーリサーチ.md"
PERPLEXITY_URL="https://www.perplexity.ai/"

echo "🔍 Daily Research Quick Launch"
echo "=============================="

# 昨日の日付を取得
YESTERDAY=$(date -v-1d '+%Y-%m-%d')
CURRENT_YEAR=$(date '+%Y')
CURRENT_MONTH=$(date '+%m')

# 昨日の日記ファイルパスを構築
DIARY_FILE="${OBSIDIAN_DIARY_PATH}/${CURRENT_YEAR}/${CURRENT_MONTH}/${YESTERDAY}.md"

echo "📅 Yesterday's diary: ${YESTERDAY}"

# 昨日の日記ファイルが存在するかチェック
if [[ ! -f "$DIARY_FILE" ]]; then
    echo "❌ Yesterday's diary file not found: $DIARY_FILE"
    exit 1
fi

# リサーチテンプレートが存在するかチェック
if [[ ! -f "$RESEARCH_TEMPLATE_PATH" ]]; then
    echo "❌ Research template not found: $RESEARCH_TEMPLATE_PATH"
    exit 1
fi

echo "📝 Building research prompt..."

# プロンプトを構築（リサーチテンプレート + 昨日の日記）
RESEARCH_PROMPT=$(cat "$RESEARCH_TEMPLATE_PATH")
DIARY_CONTENT=$(cat "$DIARY_FILE")

# 組み合わせたコンテンツをクリップボードにコピー
COMBINED_CONTENT="${RESEARCH_PROMPT}

${DIARY_CONTENT}
"

echo "$COMBINED_CONTENT" | pbcopy

echo "✅ Research prompt copied to clipboard!"
echo "📋 Content includes:"
echo "   - Research template"
echo "   - Yesterday's diary (${YESTERDAY})"

echo ""
echo "🌐 Opening Perplexity..."

# Perplexityをデフォルトブラウザで開く
open "$PERPLEXITY_URL"

echo ""
echo "✨ Ready to research!"
echo "   1. Perplexity is now open in your browser"
echo "   2. The research prompt is in your clipboard"
echo "   3. Paste (Cmd+V) and execute the research"

exit 0