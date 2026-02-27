#!/bin/bash
#===============================================================================
# 脚本名称: install_local_skills.sh
# 描述: 安装本地 Skills (通过软链接方式)
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

# 本地 Skills 列表 (自动检测脚本所在目录下的所有 skill 目录)
get_local_skills() {
    local script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    local skills=()

    for dir in "$script_dir"/*/; do
        if [ -f "$dir/SKILL.md" ]; then
            skills+=("$(basename "$dir")")
        fi
    done

    echo "${skills[@]}"
}

#===============================================================================
# 主函数
#===============================================================================
main() {
    log_info "安装本地 Skills (软链接方式)..."
    echo ""

    # 获取脚本所在目录
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

    # 创建 skills 目录
    mkdir -p ~/.claude/skills

    # 获取本地 skills
    LOCAL_SKILLS=($(get_local_skills))

    if [ ${#LOCAL_SKILLS[@]} -eq 0 ]; then
        log_warn "未找到任何本地 Skills (需要包含 SKILL.md 文件)"
        exit 0
    fi

    log_info "发现 ${#LOCAL_SKILLS[@]} 个本地 Skills"
    echo ""

    # 安装每个 skill (创建软链接)
    for skill in "${LOCAL_SKILLS[@]}"; do
        local skill_path="$SCRIPT_DIR/$skill"
        local link_path="$HOME/.claude/skills/$skill"

        # 如果链接已存在，先删除
        if [ -L "$link_path" ]; then
            rm "$link_path"
        elif [ -d "$link_path" ]; then
            log_warn "  ⚠️ $skill 已存在且不是软链接，跳过 (请手动处理)"
            continue
        fi

        # 创建软链接
        ln -s "$skill_path" "$link_path"
        log_info "  ✅ 已链接 $skill"
    done

    echo ""
    log_info "本地 Skills 安装完成"
}

#===============================================================================
# 运行主函数
#===============================================================================
main "$@"
