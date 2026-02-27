#!/bin/bash
#===============================================================================
# 脚本名称: install_official_skills.sh
# 描述: 安装官方 Claude Code Skills (来自 anthropics/skills)
#===============================================================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# 配置变量
OFFICIAL_REPO="anthropics/skills"
OFFICIAL_SKILLS=("skills/skill-creator")

# 临时目录
TMP_DIR="/tmp/claude-official-skills-$$"

#===============================================================================
# 主函数
#===============================================================================
main() {
    log_info "安装官方 Skills ($OFFICIAL_REPO)..."
    echo ""

    # 检查 gh 命令
    if ! command -v gh &> /dev/null; then
        log_error "需要 gh (GitHub CLI)，请先安装"
        exit 1
    fi

    # 创建临时目录
    mkdir -p "$TMP_DIR"
    trap "rm -rf $TMP_DIR" EXIT

    # 创建 skills 目录
    mkdir -p ~/.claude/skills

    # 克隆官方仓库
    gh repo clone "$OFFICIAL_REPO" "$TMP_DIR/skills-official" -- --depth 1 2>/dev/null || {
        log_warn "无法克隆官方 skills 仓库，跳过"
        exit 0
    }

    # 安装指定的官方 skills
    for skill_path in "${OFFICIAL_SKILLS[@]}"; do
        skill_name=$(basename "$skill_path")
        if [ -d "$TMP_DIR/skills-official/$skill_path" ]; then
            # 如果已存在，先删除
            rm -rf ~/.claude/skills/"$skill_name"
            cp -r "$TMP_DIR/skills-official/$skill_path" ~/.claude/skills/
            log_info "  ✅ 已安装 $skill_name"
        else
            log_warn "  ⚠️ 未找到 $skill_name，跳过"
        fi
    done

    echo ""
    log_info "官方 Skills 安装完成"
}

#===============================================================================
# 运行主函数
#===============================================================================
main "$@"
