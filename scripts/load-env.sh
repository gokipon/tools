#!/bin/bash

# 共通環境変数ローダー
# 各システムから呼び出して統一された環境変数を読み込む

# スクリプトのディレクトリを取得
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# .envファイルのパス
ENV_FILE="$PROJECT_ROOT/.env"

# ログ関数
log_env() {
    if [[ "${LOG_LEVEL:-INFO}" == "DEBUG" ]]; then
        echo "[ENV] $1" >&2
    fi
}

# .envファイルの存在確認
if [[ ! -f "$ENV_FILE" ]]; then
    echo "ERROR: .env file not found at: $ENV_FILE" >&2
    echo "Please copy .env.example to .env and configure your settings." >&2
    echo "FATAL: Cannot continue without environment configuration" >&2
    return 1 2>/dev/null || exit 1
fi

# .envファイルを読み込み
log_env "Loading environment variables from: $ENV_FILE"

# 空行とコメント行を除外して環境変数をエクスポート
while IFS= read -r line; do
    # 空行やコメント行をスキップ
    if [[ -z "$line" || "$line" =~ ^[[:space:]]*# ]]; then
        continue
    fi
    
    # 変数の形式をチェック（KEY=VALUE）
    if [[ "$line" =~ ^[A-Za-z_][A-Za-z0-9_]*= ]]; then
        # 環境変数として展開してエクスポート
        eval "export $line"
        var_name=$(echo "$line" | cut -d'=' -f1)
        log_env "Exported: $var_name"
    fi
done < "$ENV_FILE"

log_env "Environment variables loaded successfully"

# 必須環境変数の確認
check_required_vars() {
    local missing_vars=()
    
    for var in "$@"; do
        if [[ -z "${!var}" ]]; then
            missing_vars+=("$var")
        fi
    done
    
    if [[ ${#missing_vars[@]} -gt 0 ]]; then
        echo "ERROR: Missing required environment variables:" >&2
        printf "  - %s\n" "${missing_vars[@]}" >&2
        echo "Please configure these variables in .env file" >&2
        return 1
    fi
    
    return 0
}

# 自動的に基本的な必須変数をチェック
log_env "Checking required environment variables"
check_required_vars "OBSIDIAN_VAULT_PATH" "USER_INFO_PATH" "RESEARCH_REPORT_PATH" || {
    echo "FATAL: Environment validation failed" >&2
    return 1 2>/dev/null || exit 1
}