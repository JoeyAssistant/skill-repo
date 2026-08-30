#!/usr/bin/env bash
# agent-factory 一键部署：把 PM 工作流资产安装到目标 agent 项目
#
# 用法:
#   init-project.sh <target-project-dir>              # 一体项目（unified，默认）
#   init-project.sh <target-project-dir> --prod <path> # dev 与 prod 分离（split）
#
# 做的事:
#   1. git init（如目标还不是 git 仓）
#   2. 创建 .features/ .issues/ .claude/agents/
#   3. 复制 subagents（developer/qa/poc.md）到 .claude/agents/
#   4. 复制 agent-pm.md（PM system prompt）到 .claude/agents/（PM 提示词随项目仓走，启动命令自包含）
#   5. 复制 design-reference.md + agent-architecture.drawio 到 .claude/agents/（PM 设计阶段引用，资产落点）
#   6. --prod 时生成 .claude/agents/agent-factory.yaml（topology: split）
#   7. 检查 agent-factory CLI 可用性
#
# 可重复执行（幂等）：重跑 = 更新资产到最新版。

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET="${1:?用法: $0 <target-project-dir> [--prod <prod-root>]}"
PROD_ROOT=""

if [[ "${2:-}" == "--prod" ]]; then
  PROD_ROOT="${3:?--prod 需要路径参数}"
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
mkdir -p .features .issues .claude/agents

# 3. subagents
cp "$SCRIPT_DIR/developer.md" "$SCRIPT_DIR/qa.md" "$SCRIPT_DIR/poc.md" .claude/agents/

# 4. PM system prompt（随项目仓走，远程部署时启动命令自包含）
cp "$SCRIPT_DIR/agent-pm.md" .claude/agents/

# 5. PM 设计阶段参考资产（与 subagents 同落点，不进项目根）
cp "$SCRIPT_DIR/design-reference.md" "$SCRIPT_DIR/agent-architecture.drawio" .claude/agents/

# 6. 拓扑配置（可选）
if [[ -n "$PROD_ROOT" ]]; then
  cat > .claude/agents/agent-factory.yaml <<EOF
topology: split                  # dev 与 prod 分离：同机两个部署目录
prod:
  root: $PROD_ROOT
EOF
  echo "==> 已写入 .claude/agents/agent-factory.yaml（topology: split, prod: $PROD_ROOT）"
fi

# 6. CLI 检查
if command -v agent-factory >/dev/null 2>&1; then
  echo "==> agent-factory CLI: $(command -v agent-factory)"
else
  echo "!! agent-factory CLI 未安装。安装：pip3 install --user -e $SCRIPT_DIR"
fi

echo ""
echo "部署完成："
echo "  .claude/agents/{developer,qa,poc}.md   subagents"
echo "  .claude/agents/agent-pm.md   PM system prompt"
echo "  .claude/agents/{design-reference.md,agent-architecture.drawio}   PM 设计参考"
echo "  .features/ .issues/   状态目录"
[[ -n "$PROD_ROOT" ]] && echo "  .claude/agents/agent-factory.yaml   topology: split"
echo ""
echo "启动 PM（别名自选）："
echo "  cd $TARGET"
echo "  claude --append-system-prompt \"\$(cat .claude/agents/agent-pm.md)\""
