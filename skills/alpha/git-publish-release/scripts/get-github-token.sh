#!/usr/bin/env bash
# git-publish-release 环境管理脚本
# 功能：确保 .env 文件存在且被 .gitignore 忽略，读取 GH_TOKEN

set -euo pipefail

# 项目根目录（当前工作目录）
PROJECT_ROOT="${PROJECT_ROOT:-.}"

# .env 文件路径
ENV_FILE="$PROJECT_ROOT/.env"

# .gitignore 文件路径
GITIGNORE_FILE="$PROJECT_ROOT/.gitignore"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 确保 .env 文件存在
ensure_env_file() {
    if [[ ! -f "$ENV_FILE" ]]; then
        log_info ".env 文件不存在，正在创建..."
        cat > "$ENV_FILE" << 'EOF'
# GitHub Token for git-publish-release
# 获取方式：https://github.com/settings/tokens
# 需要的权限：repo (完整仓库访问权限)
GH_TOKEN=your_token_here
EOF
        log_warn ".env 文件已创建，请在里面添加你的 GitHub Token"
        return 1
    fi
    return 0
}

# 确保 .env 在 .gitignore 中
ensure_gitignore() {
    local env_entry=".env"

    # 如果 .gitignore 不存在，创建它
    if [[ ! -f "$GITIGNORE_FILE" ]]; then
        log_info ".gitignore 文件不存在，正在创建..."
        echo "$env_entry" > "$GITIGNORE_FILE"
        log_info ".gitignore 已创建并添加了 .env"
        return 0
    fi

    # 检查 .env 是否已在 .gitignore 中
    if grep -qx "$env_entry" "$GITIGNORE_FILE" 2>/dev/null; then
        return 0
    fi

    # 添加 .env 到 .gitignore
    log_info "将 .env 添加到 .gitignore..."
    echo "$env_entry" >> "$GITIGNORE_FILE"
    log_info ".env 已添加到 .gitignore"
    return 0
}

# 从 .env 文件读取 GH_TOKEN
read_gh_token() {
    if [[ ! -f "$ENV_FILE" ]]; then
        return 1
    fi

    # 读取 GH_TOKEN（支持带引号和不带引号）
    while IFS='=' read -r key value; do
        # 跳过注释和空行
        [[ "$key" =~ ^#.*$ || -z "$key" ]] && continue
        # 去除 key 的空格
        key=$(echo "$key" | tr -d ' ')
        # 匹配 GH_TOKEN
        if [[ "$key" == "GH_TOKEN" ]]; then
            # 去除 value 的引号和空格
            value=$(echo "$value" | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//' -e "s/^'//" -e "s/'$//" -e 's/^"//' -e 's/"$//')
            if [[ -n "$value" && "$value" != "your_token_here" ]]; then
                echo "$value"
                return 0
            fi
        fi
    done < "$ENV_FILE"

    return 1
}

# 主函数
main() {
    # 1. 确保 .gitignore 存在且包含 .env
    ensure_gitignore

    # 2. 确保 .env 文件存在
    if ! ensure_env_file; then
        log_error "请在 .env 文件中设置 GH_TOKEN 后重试"
        exit 1
    fi

    # 3. 读取并输出 GH_TOKEN
    local token
    token=$(read_gh_token) || {
        log_error "无法从 .env 文件读取有效的 GH_TOKEN"
        log_warn "请在 $ENV_FILE 中设置 GH_TOKEN=your_actual_token"
        exit 1
    }

    # 输出 token（供调用方使用）
    echo "$token"
}

# 如果直接执行脚本，运行主函数
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
