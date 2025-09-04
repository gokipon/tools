#!/bin/bash

# Git Diff Research Script - 昨日のgitコミット差分をもとにPerplexityでリサーチを実行するためのクイックコマンド

# 設定
OBSIDIAN_REPO_PATH="/Users/haruki/Library/Mobile Documents/iCloud~md~obsidian/Documents/I-think-therefore-I-am"
RESEARCH_TEMPLATE_PATH="/Users/haruki/Library/Mobile Documents/iCloud~md~obsidian/Documents/I-think-therefore-I-am/pt/デイリーリサーチ.md"
PERPLEXITY_URL="https://www.perplexity.ai/"

echo "🔍 Git Diff Research Quick Launch"
echo "==================================="

# 昨日の日付を取得
YESTERDAY=$(date -v-1d '+%Y-%m-%d')

echo "📅 Yesterday's commits: ${YESTERDAY}"

# Obsidianリポジトリに移動
cd "$OBSIDIAN_REPO_PATH" || {
    echo "❌ Cannot access Obsidian repository: $OBSIDIAN_REPO_PATH"
    exit 1
}

# gitリポジトリかチェック
if [[ ! -d ".git" ]]; then
    echo "❌ Not a git repository: $OBSIDIAN_REPO_PATH"
    exit 1
fi

# リサーチテンプレートが存在するかチェック
if [[ ! -f "$RESEARCH_TEMPLATE_PATH" ]]; then
    echo "❌ Research template not found: $RESEARCH_TEMPLATE_PATH"
    exit 1
fi

echo "📝 Getting yesterday's git commits..."

# 昨日のコミットを取得
COMMIT_HASHES=$(git log --since="$YESTERDAY 00:00:00" --until="$YESTERDAY 23:59:59" --format="%H")

if [[ -z "$COMMIT_HASHES" ]]; then
    echo "❌ No commits found for yesterday ($YESTERDAY)"
    exit 1
fi

echo "✅ Found commits for $YESTERDAY"

# git diff情報を構築
GIT_DIFF_CONTENT=""
while IFS= read -r commit_hash; do
    if [[ -n "$commit_hash" ]]; then
        echo "  📍 Processing commit: ${commit_hash:0:8}..."
        
        # コミットメッセージを取得
        COMMIT_MSG=$(git log --format="%B" -n 1 "$commit_hash")
        
        # 変更されたファイル一覧を取得
        CHANGED_FILES=$(git show --name-status "$commit_hash")
        
        # diff統計を取得
        DIFF_STAT=$(git show --stat "$commit_hash")
        
        # 実際の変更内容を取得（長すぎる場合は制限）
        ACTUAL_DIFF=$(git show --no-merges --format="" "$commit_hash" | head -n 100)
        
        GIT_DIFF_CONTENT="${GIT_DIFF_CONTENT}

=== Commit: ${commit_hash:0:8} ===

Changed Files:
${CHANGED_FILES}

Actual Changes:
${ACTUAL_DIFF}

"
    fi
done <<< "$COMMIT_HASHES"

echo "📝 Building research prompt..."

# プロンプトを構築（リサーチテンプレート + git diff情報）
RESEARCH_PROMPT=$(cat "$RESEARCH_TEMPLATE_PATH")

# 組み合わせたコンテンツをクリップボードにコピー
COMBINED_CONTENT="${RESEARCH_PROMPT}

## 昨日のgit差分情報（情報源）：
${GIT_DIFF_CONTENT}
"

echo "$COMBINED_CONTENT" | pbcopy

echo "✅ Git diff research prompt copied to clipboard!"
echo "📋 Content includes:"
echo "   - Research template"
echo "   - Yesterday's git commits and diffs (${YESTERDAY})"

echo ""
echo "🌐 Opening Perplexity..."

# Perplexityをデフォルトブラウザで開く
open "$PERPLEXITY_URL"

echo ""
echo "✨ Ready to research!"
echo "   1. Perplexity is now open in your browser"
echo "   2. The git diff research prompt is in your clipboard"
echo "   3. Paste (Cmd+V) and execute the research"

exit 0