#!/bin/bash

# 環境変数バリデーションスクリプト
# 全ワークフローで必要な環境変数が正しく設定されているかチェック

# スクリプトのディレクトリを取得
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# カラー出力用の定義
RED='\033[0;31m'
GREEN='\033[0;32m' 
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ログ関数
info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# エラーフラグ
has_errors=false
has_warnings=false

info "🔍 環境変数バリデーション開始"
echo

# 共通環境変数を読み込み
if [[ -f "$SCRIPT_DIR/load-env.sh" ]]; then
    source "$SCRIPT_DIR/load-env.sh"
else
    error "load-env.sh not found"
    exit 1
fi

echo

# 必須環境変数のチェック
info "📋 必須環境変数のチェック"

required_vars=(
    "OBSIDIAN_VAULT_PATH"
    "USER_INFO_PATH"
    "RESEARCH_REPORT_PATH"
    "RADIO_OUTPUT_PATH"
    "AZURE_OPENAI_API_KEY"
    "AZURE_OPENAI_BASE_URL"
    "AZURE_OPENAI_DEPLOYMENT"
    "PERPLEXITY_API_KEY"
)

for var in "${required_vars[@]}"; do
    if [[ -n "${!var}" ]]; then
        success "$var: 設定済み"
    else
        error "$var: 未設定"
        has_errors=true
    fi
done

echo

# オプション環境変数のチェック
info "📝 オプション環境変数のチェック"

optional_vars=(
    "LINE_NOTIFY_TOKEN"
    "RADIO_PROMPT_TEMPLATE_PATH"
    "PROMPT_TEMPLATE_PATH"
)

for var in "${optional_vars[@]}"; do
    if [[ -n "${!var}" ]]; then
        success "$var: 設定済み"
    else
        warning "$var: 未設定 (オプション)"
        has_warnings=true
    fi
done

echo

# パス存在チェック
info "📁 パス存在チェック"

path_vars=(
    "OBSIDIAN_VAULT_PATH"
    "USER_INFO_PATH"
    "RESEARCH_REPORT_PATH"
    "RADIO_OUTPUT_PATH"
)

for var in "${path_vars[@]}"; do
    path="${!var}"
    if [[ -n "$path" ]]; then
        if [[ -d "$path" ]]; then
            success "$var: ディレクトリ存在"
        else
            warning "$var: ディレクトリが存在しません ($path)"
            has_warnings=true
        fi
    fi
done

# プロンプトテンプレートファイルのチェック
if [[ -n "$RADIO_PROMPT_TEMPLATE_PATH" ]]; then
    if [[ -f "$RADIO_PROMPT_TEMPLATE_PATH" ]]; then
        success "RADIO_PROMPT_TEMPLATE_PATH: ファイル存在"
    else
        warning "RADIO_PROMPT_TEMPLATE_PATH: ファイルが存在しません ($RADIO_PROMPT_TEMPLATE_PATH)"
        has_warnings=true
    fi
fi

if [[ -n "$PROMPT_TEMPLATE_PATH" ]]; then
    if [[ -f "$PROMPT_TEMPLATE_PATH" ]]; then
        success "PROMPT_TEMPLATE_PATH: ファイル存在"
    else
        warning "PROMPT_TEMPLATE_PATH: ファイルが存在しません ($PROMPT_TEMPLATE_PATH)"
        has_warnings=true
    fi
fi

echo

# API接続テスト（オプション）
if [[ "${1:-}" == "--test-api" ]]; then
    info "🔌 API接続テスト"
    
    # Azure OpenAI接続テスト
    if [[ -n "$AZURE_OPENAI_API_KEY" && -n "$AZURE_OPENAI_BASE_URL" ]]; then
        info "Azure OpenAI接続テスト中..."
        
        response=$(curl -s -w "%{http_code}" -o /dev/null \
            -H "Authorization: Bearer $AZURE_OPENAI_API_KEY" \
            -H "Content-Type: application/json" \
            "$AZURE_OPENAI_BASE_URL/models" 2>/dev/null || echo "000")
        
        if [[ "$response" == "200" ]]; then
            success "Azure OpenAI: 接続成功"
        else
            error "Azure OpenAI: 接続失敗 (HTTP: $response)"
            has_errors=true
        fi
    fi
    
    # LINE Notify接続テスト
    if [[ -n "$LINE_NOTIFY_TOKEN" ]]; then
        info "LINE Notify接続テスト中..."
        
        response=$(curl -s -w "%{http_code}" -o /dev/null \
            -H "Authorization: Bearer $LINE_NOTIFY_TOKEN" \
            "https://notify-api.line.me/api/status" 2>/dev/null || echo "000")
        
        if [[ "$response" == "200" ]]; then
            success "LINE Notify: 接続成功"
        else
            warning "LINE Notify: 接続失敗 (HTTP: $response)"
            has_warnings=true
        fi
    fi
    
    echo
fi

# 結果サマリー
info "📊 バリデーション結果"

if [[ "$has_errors" == true ]]; then
    error "❌ エラーが検出されました。上記のエラーを修正してください。"
    echo
    error "修正方法:"
    error "1. .env ファイルを確認してください: $PROJECT_ROOT/.env"
    error "2. .env.example を参考に不足している変数を追加してください"
    error "3. API キーが正しく設定されているか確認してください"
    exit 1
elif [[ "$has_warnings" == true ]]; then
    warning "⚠️  警告がありますが、基本機能は利用可能です。"
    echo
    warning "推奨設定:"
    warning "- LINE通知を使用する場合はLINE_NOTIFY_TOKENを設定してください"
    warning "- 存在しないパスは必要に応じて作成してください"
    exit 2
else
    success "✅ 全ての環境変数が正しく設定されています！"
    echo
    success "利用可能な機能:"
    success "- ✅ Radio: ラジオ台本自動生成"
    success "- ✅ Research: 自動リサーチ"
    success "- ✅ Get-MyInfo: Safari履歴収集"
    if [[ -n "$LINE_NOTIFY_TOKEN" ]]; then
        success "- ✅ LINE通知"
    fi
    exit 0
fi