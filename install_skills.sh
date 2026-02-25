#!/bin/bash
#===============================================================================
# 脚本名称: install_skills.sh
# 描述: 安装 Claude Code Skills
# 来源:
#   - anthropics/skills (官方)
#   - JoeyAssistant/skill-repo (个人)
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
SKILLS_OFFICIAL_REPO="anthropics/skills"

SKILL_CREATOR_DIR="skills/skill-creator"
SKILLS_PERSONAL_DIRS=("doc2audio" "note-taking")

# 临时目录
TMP_DIR="/tmp/claude-skills-$$"

#===============================================================================
# 主函数
#===============================================================================
main() {
    log_info "开始安装 Claude Code Skills..."
    echo ""

    # 创建临时目录
    mkdir -p "$TMP_DIR"
    trap "rm -rf $TMP_DIR" EXIT

    # 创建 skills 目录
    mkdir -p ~/.claude/skills

    # 1. 安装官方 skill-creator
    install_official_skills

    # 2. 安装个人 skills
    install_personal_skills

    echo ""
    log_info "========================================="
    log_info "Skills 安装完成!"
    log_info "========================================="
    echo ""
    log_info "已安装的 Skills:"
    ls -1 ~/.claude/skills/ 2>/dev/null | while read dir; do
        echo "  - $dir"
    done
    echo ""
    log_warn "请重启 Claude Code 会话以加载新的 Skills"
}

#===============================================================================
# 安装官方 Skills
#===============================================================================
install_official_skills() {
    log_info "安装官方 Skills ($SKILLS_OFFICIAL_REPO)..."

    gh repo clone "$SKILLS_OFFICIAL_REPO" "$TMP_DIR/skills-official" -- --depth 1 2>/dev/null || {
        log_warn "无法克隆官方 skills 仓库，跳过"
        return
    }

    if [ -d "$TMP_DIR/skills-official/$SKILL_CREATOR_DIR" ]; then
        cp -r "$TMP_DIR/skills-official/$SKILL_CREATOR_DIR" ~/.claude/skills/
        log_info "  已安装 skill-creator"
    fi

    echo ""
}

#===============================================================================
# 安装个人 Skills
#===============================================================================
install_personal_skills() {
    log_info "安装个人 Skills (从当前目录)..."

    # 获取脚本所在目录
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

    for skill in "${SKILLS_PERSONAL_DIRS[@]}"; do
        if [ -d "$SCRIPT_DIR/$skill" ]; then
            cp -r "$SCRIPT_DIR/$skill" ~/.claude/skills/
            log_info "  已安装 $skill"
        else
            log_warn "  未找到 $skill，跳过"
        fi
    done

    echo ""
}

#===============================================================================
# 运行主函数
#===============================================================================
main "$@"
