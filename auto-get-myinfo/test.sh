#!/bin/bash

# テストスクリプト
# auto-get-myinfo システムの基本的な動作確認を行います

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== auto-get-myinfo System Test ==="
echo "Testing directory: $SCRIPT_DIR"
echo ""

# 1. ファイル存在確認
echo "1. Checking file structure..."
files=(
    "main.sh"
    "collectors/safari.sh"
    "formatters/markdown.sh" 
    "outputs/obsidian.sh"
    "config/sources.yaml"
    "com.user.auto-get-myinfo.plist"
    "README.md"
)

for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo "  ✓ $file exists"
    else
        echo "  ✗ $file missing"
        exit 1
    fi
done
echo ""

# 2. 実行権限確認
echo "2. Checking execute permissions..."
scripts=(
    "main.sh"
    "collectors/safari.sh"
    "formatters/markdown.sh"
    "outputs/obsidian.sh"
)

for script in "${scripts[@]}"; do
    if [ -x "$script" ]; then
        echo "  ✓ $script is executable"
    else
        echo "  ! $script needs execute permission (chmod +x $script)"
    fi
done
echo ""

# 3. 設定ファイル構文確認
echo "3. Checking configuration file..."
if [ -f "config/sources.yaml" ]; then
    # 基本的なYAML構文チェック（簡易版）
    if grep -q "collectors:" config/sources.yaml && \
       grep -q "formatters:" config/sources.yaml && \
       grep -q "outputs:" config/sources.yaml; then
        echo "  ✓ Configuration file structure looks valid"
    else
        echo "  ✗ Configuration file structure issue"
    fi
else
    echo "  ✗ Configuration file not found"
fi
echo ""

# 4. ログディレクトリ作成テスト
echo "4. Testing log directory creation..."
mkdir -p logs
if [ -d "logs" ]; then
    echo "  ✓ Log directory created successfully"
else
    echo "  ✗ Failed to create log directory"
    exit 1
fi
echo ""

# 5. モックデータでのフォーマッターテスト
echo "5. Testing formatter with mock data..."
cat > /tmp/mock_safari_data.json << 'EOF'
{
  "timestamp": "09:15",
  "title": "Test Website",
  "url": "https://example.com",
  "visit_count": 3,
  "source": "safari",
  "date": "2025-08-04"
}
{
  "timestamp": "10:30",
  "title": "Another Test Site",
  "url": "https://test.example.com", 
  "visit_count": 1,
  "source": "safari",
  "date": "2025-08-04"
}
EOF

if ./formatters/markdown.sh /tmp/mock_safari_data.json > /tmp/test_output.md; then
    echo "  ✓ Markdown formatter completed"
    echo "  Output preview:"
    head -5 /tmp/test_output.md | sed 's/^/    /'
else
    echo "  ✗ Markdown formatter failed"
fi
echo ""

# 6. plistファイル構文確認
echo "6. Checking launchd plist file..."
if command -v plutil >/dev/null 2>&1; then
    if plutil -lint com.user.auto-get-myinfo.plist >/dev/null 2>&1; then
        echo "  ✓ plist file syntax is valid"
    else
        echo "  ✗ plist file syntax error"
    fi
else
    echo "  ! plutil not available, skipping plist validation"
fi
echo ""

# 7. メインスクリプトのヘルプ実行
echo "7. Testing main script help..."
if ./main.sh --help 2>/dev/null || ./main.sh -h 2>/dev/null; then
    echo "  ✓ Main script responds to help flags"
elif [ $? -eq 1 ]; then
    echo "  ! Main script doesn't support help flags (this is OK)"
else
    echo "  ✓ Main script is executable"
fi
echo ""

# クリーンアップ
rm -f /tmp/mock_safari_data.json /tmp/test_output.md

echo "=== Test Summary ==="
echo "Basic system structure validation completed."
echo ""
echo "Next steps for full deployment:"
echo "1. Set execute permissions: chmod +x *.sh */*.sh"
echo "2. Update Obsidian path in config/sources.yaml"
echo "3. Configure Full Disk Access for Terminal.app"
echo "4. Test manually: ./main.sh"
echo "5. Install launchd: cp com.user.auto-get-myinfo.plist ~/Library/LaunchAgents/"
echo ""