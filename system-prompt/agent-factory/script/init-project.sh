#!/usr/bin/env bash
# agent-factory 一键部署：把 PM 工作流资产安装到目标 agent 项目
#
# 用法:
#   init-project.sh <target-project-dir>                              # 一体项目（unified，默认）
#   init-project.sh <target-project-dir> --prod <path>                # dev 与 prod 分离（split）
#   init-project.sh <target-project-dir> --base-branch <ref>          # 指定默认基线分支
#
# 做的事:
#   1. git init（如目标还不是 git 仓）
#   2. 创建 .features/ .issues/ .claude/agents/
#   3. 复制 subagents（developer/qa/qa-diagnosis/poc/patrol.md）到 .claude/agents/
#   4. 复制 agent-pm.md（PM system prompt）到 .claude/agents/（PM 提示词随项目仓走，启动命令自包含）
#   5. 复制 design-reference.md + agent-architecture.drawio 到 .claude/agents/（PM 设计阶段引用，资产落点）
#   6. agent-factory.yaml 仅在缺失时生成（topology / prod.root / base_branch）；已存在则不覆盖
#   7. 检查 agent-factory CLI 可用性
#
# 可重复执行（幂等）：重跑 = 更新资产到最新版。
# 注意：agent-factory.yaml 归用户所有，脚本只在文件缺失时生成，绝不覆盖手写配置。

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET=""
PROD_ROOT=""
BASE_BRANCH=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --prod)
      PROD_ROOT="${2:?--prod 需要路径参数}"
      shift 2
      ;;
    --base-branch)
      BASE_BRANCH="${2:?--base-branch 需要分支名}"
      shift 2
      ;;
    -*)
      echo "未知参数: $1" >&2
      exit 1
      ;;
    *)
      TARGET="$1"
      shift
      ;;
  esac
done

if [[ -z "$TARGET" ]]; then
  echo "用法: $0 <target-project-dir> [--prod <prod-root>] [--base-branch <ref>]" >&2
  exit 1
fi

TARGET="$(cd "$(dirname "$TARGET")" && pwd)/$(basename "$TARGET")"
mkdir -p "$TARGET"
cd "$TARGET"

echo "==> 目标项目: $TARGET"

# 1. git init
if [[ ! -d .git ]]; then
  git init -q
  echo "==> git init 完成"
fi

# 2. 目录结构
mkdir -p .features .issues .claude/agents .worktrees

# 2.1 .gitignore 追加 .worktrees/（feature 并行开发的 worktree 落点，不入库）
if ! grep -qx '.worktrees/' .gitignore 2>/dev/null; then
  echo '.worktrees/' >> .gitignore
  echo "==> .gitignore 已追加 .worktrees/"
fi

# 2.2 .gitignore 追加 .patrol/（patrol 巡检报告目录，过程性产物不入库）
mkdir -p .patrol
if ! grep -qx '.patrol/' .gitignore 2>/dev/null; then
  echo '.patrol/' >> .gitignore
  echo "==> .gitignore 已追加 .patrol/"
fi

# 3. subagents
cp "$SCRIPT_DIR/developer.md" "$SCRIPT_DIR/qa.md" "$SCRIPT_DIR/qa-diagnosis.md" "$SCRIPT_DIR/poc.md" "$SCRIPT_DIR/patrol.md" .claude/agents/

# 4. PM system prompt（随项目仓走，远程部署时启动命令自包含）
cp "$SCRIPT_DIR/agent-pm.md" .claude/agents/

# 5. PM 设计阶段参考资产（与 subagents 同落点，不进项目根）
cp "$SCRIPT_DIR/design-reference.md" "$SCRIPT_DIR/agent-architecture.drawio" .claude/agents/

# 6. 拓扑配置（仅在缺失时生成；已有配置归用户所有，不覆盖）
YAML_FILE=.claude/agents/agent-factory.yaml
if [[ -e "$YAML_FILE" ]]; then
  echo "==> $YAML_FILE 已存在，跳过写入（保留 base_branch 等手写配置）"
  if [[ -n "$PROD_ROOT" ]]; then
    grep -qE '^topology:[[:space:]]*split' "$YAML_FILE" \
      || echo "!! 现有 topology 非 split；如需切换请手工编辑 $YAML_FILE"
    grep -qF "root: $PROD_ROOT" "$YAML_FILE" \
      || echo "!! 现有 prod.root 与 --prod $PROD_ROOT 不一致；如需修改请手工编辑 $YAML_FILE"
  fi
  if [[ -n "$BASE_BRANCH" ]]; then
    grep -qE '^base_branch:' "$YAML_FILE" \
      || echo "!! 现有配置无 base_branch；如需设置请手工编辑 $YAML_FILE"
  fi
elif [[ -n "$PROD_ROOT" || -n "$BASE_BRANCH" ]]; then
  {
    if [[ -n "$PROD_ROOT" ]]; then
      echo "topology: split                  # dev 与 prod 分离：同机两个部署目录"
      echo "prod:"
      echo "  root: $PROD_ROOT"
    fi
    if [[ -n "$BASE_BRANCH" ]]; then
      echo "base_branch: $BASE_BRANCH          # 顶层 feature 的默认基线分支"
    fi
  } > "$YAML_FILE"
  echo "==> 已生成 $YAML_FILE"
fi

# 6. CLI 检查
if command -v agent-factory >/dev/null 2>&1; then
  echo "==> agent-factory CLI: $(command -v agent-factory)"
else
  echo "!! agent-factory CLI 未安装。安装：pip3 install --user -e $SCRIPT_DIR"
fi

echo ""
echo "部署完成："
echo "  .claude/agents/{developer,qa,qa-diagnosis,poc,patrol}.md   subagents"
echo "  .claude/agents/agent-pm.md   PM system prompt"
echo "  .claude/agents/{design-reference.md,agent-architecture.drawio}   PM 设计参考"
echo "  .features/ .issues/   状态目录"
echo "  .worktrees/   feature 并行开发 worktree 落点（已入 .gitignore）"
echo "  .patrol/   patrol 巡检报告目录（已入 .gitignore）"
[[ -n "$PROD_ROOT" ]] && echo "  .claude/agents/agent-factory.yaml   topology: split"
echo ""
echo "启动 PM（别名自选）："
echo "  cd $TARGET"
echo "  claude --append-system-prompt \"\$(cat .claude/agents/agent-pm.md)\""
