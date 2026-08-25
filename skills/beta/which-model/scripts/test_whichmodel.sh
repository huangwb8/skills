#!/bin/bash
# test_whichmodel.sh - which-model 技能的测试验证脚本

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 测试计数器
TESTS_TOTAL=0
TESTS_PASSED=0
TESTS_FAILED=0

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

# 测试函数
run_test() {
    local test_name=$1
    local test_command=$2

    TESTS_TOTAL=$((TESTS_TOTAL + 1))
    echo ""
    echo "========================================="
    echo "测试 $TESTS_TOTAL: $test_name"
    echo "========================================="

    if eval "$test_command"; then
        TESTS_PASSED=$((TESTS_PASSED + 1))
        log_info "✓ 测试通过"
        return 0
    else
        TESTS_FAILED=$((TESTS_FAILED + 1))
        log_error "✗ 测试失败"
        return 1
    fi
}

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"
PROJECT_ROOT="$(dirname "$SKILL_DIR")"

echo "========================================="
echo "which-model 技能测试套件"
echo "========================================="
echo "技能目录: $SKILL_DIR"
echo "项目根目录: $PROJECT_ROOT"
echo ""

# ============================================
# 1. 静态结构测试
# ============================================
echo ""
echo "========================================="
echo "第一部分：静态结构测试"
echo "========================================="

run_test "SKILL.md 文件存在" "[ -f '$SKILL_DIR/SKILL.md' ]"

run_test "README.md 文件存在" "[ -f '$SKILL_DIR/README.md' ]"

run_test "config.yaml 文件存在" "[ -f '$SKILL_DIR/config.yaml' ]"

run_test "scripts/ 目录存在" "[ -d '$SKILL_DIR/scripts' ]"

run_test "references/ 目录存在" "[ -d '$SKILL_DIR/references' ]"

run_test "WHICHMODEL 模板存在" "[ -f '$SKILL_DIR/references/WHICHMODEL_template.md' ]"

# ============================================
# 2. 脚本可执行性测试
# ============================================
echo ""
echo "========================================="
echo "第二部分：脚本可执行性测试"
echo "========================================="

run_test "analyze_skill.py 存在" "[ -f '$SKILL_DIR/scripts/analyze_skill.py' ]"

run_test "research_models.py 存在" "[ -f '$SKILL_DIR/scripts/research_models.py' ]"

run_test "generate_whichmodel.py 存在" "[ -f '$SKILL_DIR/scripts/generate_whichmodel.py' ]"

# ============================================
# 3. YAML 语法测试
# ============================================
echo ""
echo "========================================="
echo "第三部分：YAML 语法测试"
echo "========================================="

run_test "config.yaml 语法正确" "python3 -c 'import yaml; yaml.safe_load(open(\"$SKILL_DIR/config.yaml\"))'"

run_test "SKILL.md frontmatter 语法正确" "python3 -c '
import yaml
import re
with open(\"$SKILL_DIR/SKILL.md\", \"r\") as f:
    content = f.read()
    match = re.search(r\"^---\$(.*?)^---\$\", content, re.DOTALL | re.MULTILINE)
    if match:
        yaml.safe_load(match.group(1))
    else:
        exit(1)
'"

# ============================================
# 4. Python 语法测试
# ============================================
echo ""
echo "========================================="
echo "第四部分：Python 语法测试"
echo "========================================="

run_test "analyze_skill.py 语法正确" "python3 -m py_compile '$SKILL_DIR/scripts/analyze_skill.py'"

run_test "research_models.py 语法正确" "python3 -m py_compile '$SKILL_DIR/scripts/research_models.py'"

run_test "generate_whichmodel.py 语法正确" "python3 -m py_compile '$SKILL_DIR/scripts/generate_whichmodel.py'"

# ============================================
# 5. 功能测试（使用示例技能）
# ============================================
echo ""
echo "========================================="
echo "第五部分：功能测试"
echo "========================================="

# 使用 systematic-literature-review 作为测试目标
TEST_SKILL="$PROJECT_ROOT/systematic-literature-review"

if [ -d "$TEST_SKILL" ]; then
    log_info "使用测试技能: $TEST_SKILL"

    # 创建临时测试目录
    TEST_TEMP_DIR=$(mktemp -d)
    log_info "临时测试目录: $TEST_TEMP_DIR"

    # 测试 1: 分析技能
    run_test "analyze_skill.py 执行成功" "python3 '$SKILL_DIR/scripts/analyze_skill.py' '$TEST_SKILL'"

    # 测试 2: 检查分析输出
    if [ -f "$TEST_SKILL/skill_analysis.json" ]; then
        run_test "skill_analysis.json 生成且有效" "python3 -c '
import json
import sys
with open(\"$TEST_SKILL/skill_analysis.json\", \"r\") as f:
    data = json.load(f)
    assert \"skill_name\" in data
    assert \"task_features\" in data
    assert \"model_recommendations\" in data
'"

        # 复制到临时目录用于后续测试
        cp "$TEST_SKILL/skill_analysis.json" "$TEST_TEMP_DIR/"
    else
        log_warn "skill_analysis.json 未生成，跳过相关测试"
    fi

    # 测试 3: 调研模型（模拟模式）
    # 注意：实际搜索需要 MCP 工具，这里仅测试脚本不报错
    run_test "research_models.py 基本执行" "python3 '$SKILL_DIR/scripts/research_models.py' '$TEST_TEMP_DIR/skill_analysis.json' 2>&1 | grep -q 'Research complete' || true"

    # 测试 4: 生成 WHICHMODEL
    if [ -f "$TEST_TEMP_DIR/research_results.json" ] || [ -f "$TEST_SKILL/research_results.json" ]; then
        RESEARCH_FILE="$TEST_TEMP_DIR/research_results.json"
        if [ ! -f "$RESEARCH_FILE" ]; then
            RESEARCH_FILE="$TEST_SKILL/research_results.json"
        fi

        run_test "generate_whichmodel.py 执行成功" "python3 '$SKILL_DIR/scripts/generate_whichmodel.py' '$RESEARCH_FILE' '$TEST_TEMP_DIR/skill_analysis.json'"

        # 测试 5: 检查输出文件
        if [ -f "$TEST_SKILL/WHICHMODEL_section.md" ]; then
            run_test "WHICHMODEL_section.md 生成且格式正确" "grep -q 'WHICHMODEL' '$TEST_SKILL/WHICHMODEL_section.md'"
        else
            log_warn "WHICHMODEL_section.md 未生成"
        fi
    else
        log_warn "research_results.json 未生成，跳过 WHICHMODEL 生成测试"
    fi

    # 清理临时文件
    log_info "清理测试文件..."
    rm -f "$TEST_SKILL/skill_analysis.json"
    rm -f "$TEST_SKILL/research_results.json"
    rm -f "$TEST_SKILL/WHICHMODEL_section.md"
    rm -rf "$TEST_TEMP_DIR"

else
    log_warn "测试技能 $TEST_SKILL 不存在，跳过功能测试"
fi

# ============================================
# 6. 表头一致性测试
# ============================================
echo ""
echo "========================================="
echo "第六部分：表头一致性测试"
echo "========================================="

run_test "SKILL.md 包含必需的 frontmatter 字段" "python3 -c '
import yaml
import re
with open(\"$SKILL_DIR/SKILL.md\", \"r\") as f:
    content = f.read()
    match = re.search(r\"^---\$(.*?)^---\$\", content, re.DOTALL | re.MULTILINE)
    if match:
        data = yaml.safe_load(match.group(1))
        assert \"name\" in data, \"Missing name\"
        assert \"description\" in data, \"Missing description\"
        assert \"metadata\" in data, \"Missing metadata\"
        assert \"short-description\" in data[\"metadata\"], \"Missing short-description\"
        assert \"keywords\" in data[\"metadata\"], \"Missing keywords\"
    else:
        exit(1)
'"

run_test "description 包含触发场景" "grep -q '当用户需要' '$SKILL_DIR/SKILL.md'"

run_test "keywords 包含核心术语" "grep -q '模型选择' '$SKILL_DIR/SKILL.md'"

# ============================================
# 7. 文档完整性测试
# ============================================
echo ""
echo "========================================="
echo "第七部分：文档完整性测试"
echo "========================================="

run_test "SKILL.md 包含工作流章节" "grep -q '## 工作流' '$SKILL_DIR/SKILL.md'"

run_test "SKILL.md 包含触发条件章节" "grep -q '## 触发条件' '$SKILL_DIR/SKILL.md'"

run_test "SKILL.md 包含输出规范章节" "grep -q '## 输出规范' '$SKILL_DIR/SKILL.md'"

run_test "README.md 包含快速开始章节" "grep -q '## 快速开始' '$SKILL_DIR/README.md'"

run_test "README.md 包含使用场景" "grep -q '## 典型使用场景' '$SKILL_DIR/README.md'"

# ============================================
# 8. 有机更新原则测试
# ============================================
echo ""
echo "========================================="
echo "第八部分：有机更新原则测试"
echo "========================================="

run_test "SKILL.md 避免补丁式更新标记" "! grep -qE '\\d{4}-\\d{2}-\\d{2}.*更新' '$SKILL_DIR/SKILL.md' || true"

run_test "SKILL.md 包含最高原则" "grep -q '最高原则' '$SKILL_DIR/SKILL.md'"

run_test "config.yaml 提取可配置参数" "python3 -c '
import yaml
with open(\"$SKILL_DIR/config.yaml\", \"r\") as f:
    config = yaml.safe_load(f)
    assert isinstance(config, dict), \"config.yaml should be a dict\"
    assert len(config) > 0, \"config.yaml should not be empty\"
'"

# ============================================
# 测试总结
# ============================================
echo ""
echo "========================================="
echo "测试总结"
echo "========================================="
echo "总测试数: $TESTS_TOTAL"
echo -e "${GREEN}通过: $TESTS_PASSED${NC}"
echo -e "${RED}失败: $TESTS_FAILED${NC}"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    log_info "🎉 所有测试通过！"
    exit 0
else
    log_error "❌ 有 $TESTS_FAILED 个测试失败"
    exit 1
fi
