#!/usr/bin/env bash
#
# install.sh - 快速安装脚本
#
# 用法:
#   curl -fsSL https://raw.githubusercontent.com/huangwb8/skills/main/@install/install.sh | bash
#   wget -qO- https://raw.githubusercontent.com/huangwb8/skills/main/@install/install.sh | bash
#
# 默认行为: python3 install-bensz-skills/scripts/install.py --remote --auto
#

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
info() { echo -e "${BLUE}[INFO]${NC} $1"; }
success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; }

# 检查命令是否存在
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# 主安装器 URL
INSTALLER_REPO="https://github.com/huangwb8/skills"
INSTALLER_RAW_BASE="https://raw.githubusercontent.com/huangwb8/skills/main"
INSTALLER_SCRIPT_PATH="install-bensz-skills/scripts/install.py"

# 临时目录
TEMP_DIR=$(mktemp -d 2>/dev/null || mktemp -d -t 'install-bensz-skills')
trap "rm -rf $TEMP_DIR" EXIT

info "开始安装 bensz 技能..."
echo ""

# 检查 Python
if ! command_exists python3 && ! command_exists python; then
    error "未找到 Python。请先安装 Python 3.7 或更高版本。"
    exit 1
fi

# 确定 Python 命令
PYTHON_CMD="python3"
if ! command_exists python3; then
    PYTHON_CMD="python"
fi

PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | awk '{print $2}')
info "检测到 Python: $PYTHON_VERSION"

# 检查 pip (用于安装 pyyaml)
if ! $PYTHON_CMD -m pip --version >/dev/null 2>&1; then
    warn "pip 未安装，尝试安装 PyYAML 可能失败..."
fi

# 创建临时目录结构
INSTALLER_DIR="$TEMP_DIR/install-bensz-skills/scripts"
mkdir -p "$INSTALLER_DIR"

# 下载安装脚本
INSTALLER_URL="$INSTALLER_RAW_BASE/$INSTALLER_SCRIPT_PATH"
info "下载安装脚本: $INSTALLER_URL"

if command_exists curl; then
    curl -fsSL "$INSTALLER_URL" -o "$INSTALLER_DIR/install.py"
elif command_exists wget; then
    wget -q "$INSTALLER_URL" -O "$INSTALLER_DIR/install.py"
else
    error "未找到 curl 或 wget。请安装其中之一后重试。"
    exit 1
fi

# 下载 i18n 模块
I18N_URL="$INSTALLER_RAW_BASE/install-bensz-skills/scripts/i18n.py"
info "下载 i18n 模块: $I18N_URL"

if command_exists curl; then
    curl -fsSL "$I18N_URL" -o "$INSTALLER_DIR/i18n.py"
elif command_exists wget; then
    wget -q "$I18N_URL" -O "$INSTALLER_DIR/i18n.py"
fi

# 检查是否需要下载 config.yaml
# 在远程模式下，config.yaml 需要从本地获取，所以我们需要模拟整个目录结构
CONFIG_DIR="$TEMP_DIR/install-bensz-skills"
mkdir -p "$CONFIG_DIR"

CONFIG_URL="$INSTALLER_RAW_BASE/install-bensz-skills/config.yaml"
info "下载配置文件: $CONFIG_URL"

if command_exists curl; then
    curl -fsSL "$CONFIG_URL" -o "$CONFIG_DIR/config.yaml"
elif command_exists wget; then
    wget -q "$CONFIG_URL" -O "$CONFIG_DIR/config.yaml"
fi

# 尝试安装 PyYAML（如果未安装）
if ! $PYTHON_CMD -c "import yaml" >/dev/null 2>&1; then
    info "安装 PyYAML 依赖..."
    $PYTHON_CMD -m pip install pyyaml --user -q || {
        warn "PyYAML 安装失败，将尝试继续..."
    }
fi

echo ""
info "运行安装程序 (远程自动模式)..."
echo ""

# 运行安装脚本（远程自动模式）
cd "$TEMP_DIR"
$PYTHON_CMD install-bensz-skills/scripts/install.py --remote --auto

EXIT_CODE=$?

echo ""
if [ $EXIT_CODE -eq 0 ]; then
    success "安装完成！"
    echo ""
    info "提示: 技能已安装到 ~/.claude/skills/ 和 ~/.codex/skills/"
else
    error "安装失败 (退出代码: $EXIT_CODE)"
    echo ""
    info "如需帮助，请访问: $INSTALLER_REPO/issues"
fi

exit $EXIT_CODE
