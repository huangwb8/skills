#!/bin/bash
#
# Awesome Code - Git 工作流辅助脚本
#
# 功能：
# - Conventional Commits 提交
# - PR 模板生成
# - 分支管理辅助
#

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# 检查是否在 Git 仓库中
check_git_repo() {
    if ! git rev-parse --git-dir > /dev/null 2>&1; then
        print_error "当前目录不是 Git 仓库"
        exit 1
    fi
}

# Conventional Commits 提交
commit_conventional() {
    check_git_repo

    print_info "Conventional Commits 提交向导"

    # 选择类型
    echo ""
    echo "选择提交类型："
    echo "  1) feat     - 新功能"
    echo "  2) fix      - Bug 修复"
    echo "  3) docs     - 文档变更"
    echo "  4) style    - 代码格式（不影响功能）"
    echo "  5) refactor - 重构"
    echo "  6) perf     - 性能优化"
    echo "  7) test     - 测试相关"
    echo "  8) chore    - 构建/工具变更"
    echo "  9) ci       - CI 配置"
    read -p "选择 [1-9]: " type_choice

    case $type_choice in
        1) type="feat" ;;
        2) type="fix" ;;
        3) type="docs" ;;
        4) type="style" ;;
        5) type="refactor" ;;
        6) type="perf" ;;
        7) type="test" ;;
        8) type="chore" ;;
        9) type="ci" ;;
        *)
            print_error "无效选择"
            exit 1
            ;;
    esac

    # 输入范围（可选）
    read -p "输入范围（可选，按 Enter 跳过）: " scope

    # 输入主题
    read -p "输入提交主题（必填）: " subject

    if [ -z "$subject" ]; then
        print_error "提交主题不能为空"
        exit 1
    fi

    # 构建提交标题
    if [ -n "$scope" ]; then
        commit_title="$type($scope): $subject"
    else
        commit_title="$type: $subject"
    fi

    # 输入正文（可选）
    echo ""
    read -p "输入提交正文（可选，按 Enter 跳过）: " body

    # 输入 Footer（可选）
    read -p "输入 Footer（可选，如 Closes #123，按 Enter 跳过）: " footer

    # 构建完整提交消息
    commit_message="$commit_title"

    if [ -n "$body" ]; then
        commit_message="$commit_message"$'\n\n'"$body"
    fi

    if [ -n "$footer" ]; then
        commit_message="$commit_message"$'\n\n'"$footer"
    fi

    # 显示提交消息预览
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "$commit_message"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""

    read -p "确认提交？[y/N] " confirm

    if [ "$confirm" = "y" ] || [ "$confirm" = "Y" ]; then
        git commit -m "$commit_message"
        print_success "提交成功！"
    else
        print_warning "已取消提交"
    fi
}

# 创建新分支
create_branch() {
    check_git_repo

    print_info "创建新分支"

    # 选择分支类型
    echo ""
    echo "选择分支类型："
    echo "  1) feature  - 功能开发"
    echo "  2) bugfix   - Bug 修复"
    echo "  3) hotfix   - 紧急修复"
    echo "  4) release  - 发布版本"
    read -p "选择 [1-4]: " type_choice

    case $type_choice in
        1) prefix="feature" ;;
        2) prefix="bugfix" ;;
        3) prefix="hotfix" ;;
        4) prefix="release" ;;
        *)
            print_error "无效选择"
            exit 1
            ;;
    esac

    # 输入分支名称
    read -p "输入分支名称: " branch_name

    if [ -z "$branch_name" ]; then
        print_error "分支名称不能为空"
        exit 1
    fi

    full_branch_name="$prefix/$branch_name"

    # 确保在 main 分支
    current_branch=$(git branch --show-current)
    if [ "$current_branch" != "main" ] && [ "$current_branch" != "master" ]; then
        print_warning "当前不在 main/master 分支"
        read -p "是否切换到 main 分支？[y/N] " switch_confirm
        if [ "$switch_confirm" = "y" ] || [ "$switch_confirm" = "Y" ]; then
            git checkout main || git checkout master
        fi
    fi

    # 拉取最新代码
    print_info "拉取最新代码..."
    git pull

    # 创建并切换到新分支
    print_info "创建分支: $full_branch_name"
    git checkout -b "$full_branch_name"

    print_success "分支创建成功！当前分支: $full_branch_name"
}

# PR 模板生成
generate_pr_template() {
    cat << 'EOF'
## 📋 变更类型
- [ ] `feat` 新功能
- [ ] `fix` Bug 修复
- [ ] `refactor` 重构
- [ ] `docs` 文档
- [ ] `style` 代码格式
- [ ] `test` 测试
- [ ] `chore` 构建/工具

## 📝 变更说明
<!-- 简要描述这个 PR 的目的和实现方式 -->



## 🧪 测试
- [ ] 添加了单元测试
- [ ] 添加了集成测试
- [ ] 手动测试通过
- [ ] 性能测试通过（如适用）

## ✅ 检查清单
- [ ] 代码符合团队规范
- [ ] 自我审查完成
- [ ] 注释充分且准确
- [ ] 文档已更新
- [ ] 无新的警告产生
- [ ] 测试覆盖率未降低

## 📸 截图/演示（可选）
<!-- 添加 UI 变更的截图 -->



## 🔗 相关链接
- 关联 Issue:

EOF
}

# 创建 PR
create_pr() {
    check_git_repo

    # 检查是否安装了 GitHub CLI
    if ! command -v gh &> /dev/null; then
        print_error "未安装 GitHub CLI (gh)"
        print_info "安装: https://cli.github.com/"
        exit 1
    fi

    print_info "创建 Pull Request"

    # 获取当前分支
    current_branch=$(git branch --show-current)
    base_branch="main"

    # 检查是否有未推送的提交
    if git log origin/"$current_branch".."$current_branch" &> /dev/null; then
        print_warning "有未推送的提交"
        read -p "是否先推送？[y/N] " push_confirm
        if [ "$push_confirm" = "y" ] || [ "$push_confirm" = "Y" ]; then
            git push -u origin "$current_branch"
        fi
    fi

    # 生成 PR 标题（基于最近的提交）
    pr_title=$(git log -1 --pretty=%s)

    # 生成 PR 模板
    pr_body=$(generate_pr_template)

    # 使用 gh 创建 PR
    print_info "创建 PR: $current_branch -> $base_branch"
    echo "$pr_body" | gh pr create \
        --base "$base_branch" \
        --title "$pr_title" \
        --body-file -

    print_success "PR 创建成功！"
}

# 显示帮助
show_help() {
    cat << EOF
Awesome Code - Git 工作流辅助脚本

用法:
    $0 <command> [options]

命令:
    commit      使用 Conventional Commits 规范提交
    branch      创建新分支（遵循命名规范）
    pr          创建 Pull Request
    template    输出 PR 模板

示例:
    $0 commit           # 交互式提交
    $0 branch           # 创建新分支
    $0 pr               # 创建 PR
    $0 template > pr.md # 保存 PR 模板

更多信息请参考:
    https://github.com/anthropics/skills
EOF
}

# 主函数
main() {
    case "${1:-}" in
        commit)
            commit_conventional
            ;;
        branch)
            create_branch
            ;;
        pr)
            create_pr
            ;;
        template)
            generate_pr_template
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            print_error "未知命令: ${1:-}"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

main "$@"
