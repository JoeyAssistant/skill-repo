# agent-factory 环境拓扑统一 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 删除 `_incoming` 跨环境机制，新增 `topology` 配置（unified/split）与 prod 只读访问，提供协作仓零足迹部署方案。

**Architecture:** 纯 prompt/文档改动（agent-pm.md / qa.md / developer.md / README.md），CLI 与 schema 不动。提示词净减约 307 行。

**Tech Stack:** Markdown 编辑（Edit 工具 + python 正则删除整章）、grep 验证。

**设计文档:** `docs/superpowers/specs/2026-08-30-agent-factory-single-env-design.md`

**工作目录:** 所有命令在 `system-prompt/agent-factory/` 下执行。

---

### Task 1: agent-pm.md — 删除跨环境机制两章及连带引用

**Files:**
- Modify: `agent-pm.md`

- [ ] **Step 1: 删除两章正文（§生产环境模式 + §跨环境 Issue 处理）**

按章节标题正则删除，行号无关：

```bash
python3 - <<'EOF'
import re
p = 'agent-pm.md'
s = open(p).read()
s2 = re.sub(r'\n## 生产环境模式.*?\n## 任务调度', '\n## 任务调度', s, flags=re.S)
assert s2 != s, '未匹配到删除范围'
open(p, 'w').write(s2)
EOF
```

- [ ] **Step 2: 验证章节已删、接缝干净**

```bash
grep -n "^## " agent-pm.md
```

预期：`## 生产环境模式`、`## 跨环境 Issue 处理` 不在列表中；`## Issue 命令` 与 `## 任务调度` 之间只剩一组 `---` 分隔线（无连续两个 `---`，若有双分隔线则手工删一个）。

- [ ] **Step 3: 删除 TOC 中两章条目**

```bash
python3 - <<'EOF'
import re
p = 'agent-pm.md'
s = open(p).read()
s2 = re.sub(r'\n  - \[生产环境模式\].*?\n  - \[任务调度\]', '\n  - [任务调度]', s, flags=re.S)
assert s2 != s, 'TOC 未匹配'
open(p, 'w').write(s2)
EOF
```

- [ ] **Step 4: 删除"允许 PM 自己做的事"中的跨环境条目（整行）**

old（Edit 工具，删除该行）：

```
  - **跨环境 issue**（来自 `_incoming/`）：确认 `snapshot/{log,data}` 已就位，作为 QA 复现依据
```

- [ ] **Step 5: 删除调度模板中的引用行（整行含其后空行）**

old（Edit 工具，删除）：

```
跨环境 Issue 验证调度 prompt 见 §跨环境 Issue 处理。

```

- [ ] **Step 6: 日常巡检删 `_incoming` 步骤并重排编号**

old:

```
1. `git pull` 拉取最新代码
2. 检查 `.issues/_incoming/` 是否有新的生产环境报告，如有按 §跨环境 Issue 处理 > _incoming 扫描 流程处理
3. 读取 `.features/index.yaml` 和 `.issues/index.yaml`
4. 汇报：
   - 来自生产环境的新报告数
   - open issue 待 triage 数
```

new:

```
1. `git pull` 拉取最新代码
2. 读取 `.features/index.yaml` 和 `.issues/index.yaml`
3. 汇报：
   - open issue 待 triage 数
```

同时把该列表的 `5. 询问用户需要做什么` 改为 `4. 询问用户需要做什么`。

- [ ] **Step 7: 证据示例两处 NOTES.md 改为 README.md**

old: `` `git show 986e7b1 --stat` 看 diff，可能只是登记了 NOTES.md | ``
new: `` `git show 986e7b1 --stat` 看 diff，可能只是登记了 README.md | ``

old: `- 只改了 NOTES.md (+84) → 不符合"实现收入模块"描述 → 不采信，回去问 developer`
new: `- 只改了 README.md (+84) → 不符合"实现收入模块"描述 → 不采信，回去问 developer`

- [ ] **Step 8: grep 验证**

```bash
grep -n "_incoming\|生产环境\|跨环境\|snapshot\|NOTES" agent-pm.md
```

预期：无输出（exit 1）。

- [ ] **Step 9: Commit**

```bash
git add agent-pm.md
git commit -m "refactor(pm-prompt): 删除 _incoming 跨环境机制两章及连带引用"
```

---

### Task 2: agent-pm.md — 新增 topology 检测与 prod 只读访问

**Files:**
- Modify: `agent-pm.md`

- [ ] **Step 1: 模式检测加第 3 项**

old:

```
1. 当前目录有 `.features/` → 已初始化，继续
2. 都没有 → 询问用户："初始化项目？" → 创建 `.features/` `.issues/`
```

new:

```
1. 当前目录有 `.features/` → 已初始化，继续
2. 都没有 → 询问用户："初始化项目？" → 创建 `.features/` `.issues/`
3. 读 `.claude/agents/agent-factory.yaml`（无此文件则跳过）的 `topology`：
   - `unified`（或无 topology 键）→ dev 与 prod 一体，无特殊行为
   - `split` 且 `prod.root` 完整 → 激活 §prod 只读访问
   - `split` 但 `prod.root` 缺失，或 `unified` 却带 prod → 配置矛盾，向用户报错并提示修配置
```

- [ ] **Step 2: 在模式检测之后插入新小节**

old:

```
项目自带的 `.claude/agents/` 优先使用。

---

## Issue 命令
```

new:

```
项目自带的 `.claude/agents/` 优先使用。

---

## prod 只读访问

`topology: split`（dev 与 prod 分离）时生效。prod 路径来自 `.claude/agents/agent-factory.yaml` 的 `prod.root`；log/data 默认按 `<root>/log`、`<root>/data` 约定发现，可被 `prod.log` / `prod.data` 覆盖。

- **直读**：定位问题、收集证据时直接读取 prod 下的 log/data，**不 cp、不建 snapshot**；引用证据时带文件路径 + 行号
- **只读约束**：对 prod 路径下任何文件禁止写入 / 修改 / 删除（包括加日志、改数据）。prod 是运行现场，取证只读
- **调度传递**：调度 QA / developer 涉及 prod 取证时，调度 prompt 中必须注明 prod 路径与只读约束（subagent 不读配置文件）

---

## Issue 命令
```

- [ ] **Step 3: TOC 加条目**

old:

```
  - [模式检测](#模式检测)
  - [Issue 命令](#issue-命令)
```

new:

```
  - [模式检测](#模式检测)
  - [prod 只读访问](#prod-只读访问)
  - [Issue 命令](#issue-命令)
```

- [ ] **Step 4: 验证**

```bash
grep -n "topology\|prod 只读访问" agent-pm.md
```

预期：模式检测 1 处 + 小节标题 1 处 + TOC 1 处。

- [ ] **Step 5: Commit**

```bash
git add agent-pm.md
git commit -m "feat(pm-prompt): topology 配置检测与 prod 只读访问小节"
```

---

### Task 3: qa.md — 删模式三 + 修齐模式二

**Files:**
- Modify: `qa.md`

- [ ] **Step 1: 角色约束——删生产环境两条、修诊断条目**

old:

```
- 验收模式下你只更新 feature 目录下的 `QA-REPORT.md`
- 诊断模式下你只更新 issue 目录下 `NOTES.md` 的 `QA Diagnosis` 章节，不修改其他章节
- 生产环境诊断模式下你创建 `.issues/_incoming/` 报告，不修改 `index.md`
- 生产环境诊断模式下你只做只读操作，不修改代码或生产数据
```

new:

```
- 验收模式下你只更新 feature 目录下的 `QA-REPORT.md`
- 诊断模式下你只通过 CLI 更新 issue 的 `root_cause` / `fix_plan`（ISSUE.yaml），不做 transition
```

- [ ] **Step 2: 删工作模式中的模式三定义**

old:

```
### 模式二：诊断模式（Issue Diagnosis）

用户使用中发现问题，PM 调度你进行根因分析和举一反三。

### 模式三：生产环境诊断模式（Production Diagnosis）

生产环境发现问题后，在生产环境直接定位根因、收集快照、提交报告。
```

new:

```
### 模式二：诊断模式（Issue Diagnosis）

用户使用中发现问题，PM 调度你进行根因分析和举一反三。
```

- [ ] **Step 3: 修诊断模式输入格式 Instructions**

old:

```
## Instructions
1. Read NOTES.md for issue description and reproduction steps
2. Reproduce the issue
3. Diagnose root cause (logs, code, data flow)
4. Audit log auditability for this issue
5. Search for similar patterns
6. Write diagnosis to NOTES.md (fill QA Diagnosis section, do not modify other sections)
7. Return diagnosis report

Note: QA only updates NOTES.md in the issue directory. Issue status in index.md is managed by PM.
```

new:

```
## Instructions
1. Read ISSUE.yaml (`agent-factory issue show <id>`) for issue description and reproduction steps
2. Reproduce the issue
3. Diagnose root cause (logs, code, data flow)
4. Audit log auditability for this issue
5. Search for similar patterns
6. Write diagnosis back via CLI (root_cause / fix_plan, see 诊断工作流程)
7. Return diagnosis report

Note: QA only updates root_cause / fix_plan via CLI. Issue status in index.yaml is managed by PM.
```

- [ ] **Step 4: 删除输入格式中的模式三整块**

```bash
python3 - <<'EOF'
import re
p = 'qa.md'
s = open(p).read()
s2 = re.sub(r'\n### 模式三：生产环境诊断（仅诊断，PM 接管提交）.*?\n## 按 Agent Type', '\n## 按 Agent Type', s, flags=re.S)
assert s2 != s, '模式三块未匹配'
open(p, 'w').write(s2)
EOF
```

- [ ] **Step 5: 修诊断工作流程步骤 1-2**

old: `1. **复现问题**：按 NOTES.md 中的 Steps to Reproduce 复现问题`
new: `1. **复现问题**：按 ISSUE.yaml 的 scenario（复现步骤）复现问题`

old:

```
   - **日志缺失/不足** → 在 NOTES.md 的 `QA Diagnosis` 章节标注 `Log Auditability: insufficient` 并给出补充建议（缺什么日志、应在哪个分支加），**优先反馈给 developer 补日志后再继续深度诊断**。避免在日志不足的情况下硬推根因，导致诊断不可靠
```

new:

```
   - **日志缺失/不足** → 在返回报告中标注 `log_auditability: insufficient` 并给出补充建议（缺什么日志、应在哪个分支加），**优先反馈给 developer 补日志后再继续深度诊断**。避免在日志不足的情况下硬推根因，导致诊断不可靠
```

- [ ] **Step 6: 合并工作流程步骤 6/7**

old:

```
6. **写入 ISSUE.yaml**：将诊断结论填入 `QA Diagnosis` 章节（不修改其他章节）
7. **通过 CLI 写回**：
   - `agent-factory issue set <id> root_cause "<根因>"`
   - `agent-factory issue set <id> fix_plan "<方案：问题分析 + bugfix 方向 + feature 方向 + QA 建议>"`
8. **返回诊断报告**：将结构化结果返回给 PM（QA 不预判 bugfix/feature 路径，不写 result，不做 transition）
```

new:

```
6. **通过 CLI 写回诊断结论**：
   - `agent-factory issue set <id> root_cause "<根因，含具体 file:line>"`
   - `agent-factory issue set <id> fix_plan "<方案：问题分析 + bugfix 方向 + feature 方向 + QA 建议>"`（长方案用 `--file`）
7. **返回诊断报告**：将结构化结果返回给 PM（QA 不预判 bugfix/feature 路径，不写 result，不做 transition）
```

- [ ] **Step 7: 删除 §NOTES.md 写入规范壳，fix_plan 写法升为二级标题**

```bash
python3 - <<'EOF'
import re
p = 'qa.md'
s = open(p).read()
s2 = re.sub(r'\n## NOTES\.md 写入规范.*?\n### fix_plan 写法', '\n## fix_plan 写法', s, flags=re.S)
assert s2 != s, 'NOTES 壳未匹配'
open(p, 'w').write(s2)
EOF
```

- [ ] **Step 8: index.md 全部替换为 index.yaml**

Edit 工具 replace_all：`index.md` → `index.yaml`（预期命中 2 处：角色约束"你不检查 index.md"、诊断 Note 行）。

- [ ] **Step 9: grep 验证**

```bash
grep -n "_incoming\|NOTES\|模式三\|生产环境\|index.md" qa.md
```

预期：无输出（exit 1）。

- [ ] **Step 10: Commit**

```bash
git add qa.md
git commit -m "refactor(qa-prompt): 删生产环境诊断模式，诊断流程对齐 ISSUE.yaml + CLI"
```

---

### Task 4: developer.md — 修齐 index.md 与状态流转

**Files:**
- Modify: `developer.md`

- [ ] **Step 1: index.md 全部替换为 index.yaml**

Edit 工具 replace_all：`index.md` → `index.yaml`（预期命中 5 处）。

- [ ] **Step 2: 修状态流转行**

old: `4. **更新状态**：开始编码前，将 \`{Root}/.features/index.md\` 中对应需求状态更新为 \`implementing\`；开发完成后更新为 \`done\``

new: `4. **更新状态**：开始编码前，将 \`{Root}/.features/index.yaml\` 中对应需求状态更新为 \`implementing\`；开发完成后更新为 \`qa-reviewing\``

（若 Step 1 的 replace_all 已把此行 index.md 改为 index.yaml，old 里相应调整。）

- [ ] **Step 3: grep 验证**

```bash
grep -n "index.md\|更新为 \`done\`" developer.md
```

预期：无输出（exit 1）。注意：`生产环境`（运行时日志语境）保留，不在检查项内。

- [ ] **Step 4: Commit**

```bash
git add developer.md
git commit -m "fix(dev-prompt): index.md 修正为 index.yaml，完成状态修正为 qa-reviewing"
```

---

### Task 5: README.md — 删协作章节 + 新增零足迹部署

**Files:**
- Modify: `README.md`

- [ ] **Step 1: 删除"生产 ↔ 开发协作"章节**

```bash
python3 - <<'EOF'
import re
p = 'README.md'
s = open(p).read()
s2 = re.sub(r'\n### 生产 ↔ 开发协作.*?\n## 安装', '\n## 安装', s, flags=re.S)
assert s2 != s, '协作章节未匹配'
open(p, 'w').write(s2)
EOF
```

- [ ] **Step 2: 在 `## 使用` 之前插入零足迹部署章节**

old:

```
## 使用
```

new:

```
## 零足迹部署（协作项目）

团队协作仓不能出现 agent-factory 痕迹时的部署方式。

### 1. 安装资产与本地排除

subagents 与配置统一放在 `.claude/agents/`（agent-factory 资产落点）：

```bash
mkdir -p <project>/.claude/agents
cp developer.md qa.md poc.md <project>/.claude/agents/
```

状态目录与（如被跟踪的）`.claude/` 加入本地排除——**不写 .gitignore**（.gitignore 本身进仓，暴露痕迹）：

```bash
printf '.features/\n.issues/\n.claude/\n' >> <project>/.git/info/exclude
```

### 2. 环境配置（dev 与 prod 分离的项目）

创建 `<project>/.claude/agents/agent-factory.yaml`：

```yaml
topology: split                  # dev 与 prod 分离：同机两个部署目录
prod:
  root: /abs/path/to/prod-deploy
```

一体项目无需此文件（默认 unified）。

### 3. 启动

别名自选；split 时 `--add-dir` 授权读取 prod：

```bash
pm() {
  local prod_root=$(grep -E '^\s*root:' .claude/agents/agent-factory.yaml 2>/dev/null | head -1 | awk '{print $2}')
  claude-glm-skip-perms \
    --append-system-prompt "$(cat <agent-factory>/agent-pm.md)" \
    ${prod_root:+--add-dir "$prod_root"}
}
```

### 4. prod 只读硬兜底（建议）

用户级 `~/.claude/settings.json` 添加（路径限定，不影响其他项目）：

```json
{
  "permissions": {
    "deny": ["Edit(/abs/path/to/prod/**)", "Write(/abs/path/to/prod/**)"]
  }
}
```

> agent-factory 资产（prompt + subagents + CLI）可在任意 Claude Code 会话中使用，驱动方式不限。

## 使用
```

- [ ] **Step 3: 验证**

```bash
grep -n "_incoming\|生产环境\|生产 ↔" README.md
```

预期：无输出（exit 1）。

```bash
grep -n "零足迹部署\|topology" README.md
```

预期：新章节标题与配置示例命中。

- [ ] **Step 4: Commit**

```bash
git add README.md
git commit -m "docs(readme): 删生产↔开发协作章节，新增零足迹部署与 topology 配置说明"
```

---

### Task 6: 全局验证

- [ ] **Step 1: 跨环境术语零残留**

```bash
grep -n "_incoming\|NOTES.md\|REQUIREMENTS.md\|生产环境\|跨环境\|snapshot" agent-pm.md qa.md README.md; echo "exit=$?"
```

预期：exit=1（无匹配）。

- [ ] **Step 2: index.md 零残留（全部 prompt 文件）**

```bash
grep -n "index.md" agent-pm.md qa.md developer.md poc.md; echo "exit=$?"
```

预期：exit=1（无匹配）。

- [ ] **Step 3: 行数 sanity**

```bash
wc -l agent-pm.md qa.md
```

预期：agent-pm.md ≈ 730±8，qa.md ≈ 339±8（设计估算 729/339）。

- [ ] **Step 4: TOC 与章节一致性抽查**

```bash
grep -c "^  - \[" agent-pm.md && grep -n "^## " agent-pm.md
```

预期：TOC 二级条目数与 `## ` 章节数一致（含 prod 只读访问，不含已删两章）。

- [ ] **Step 5: 运行时 E2E（人工，对应设计 §6）**

准备 fixture：`mkdir -p /tmp/e2e-prod/log /tmp/e2e-prod/data`，写入示例日志与数据文件；目标项目创建 `.claude/agents/agent-factory.yaml`（`topology: split` + `prod.root: /tmp/e2e-prod`），按 README 零足迹部署启动 PM，依次验证：

1. 报一个 prod 问题 → PM 应 `agent-factory issue new` 提单，并直读 `/tmp/e2e-prod/log` 定位，结论引用路径+行号
2. 诱导 PM 写 prod 文件（"帮我在 /tmp/e2e-prod/data 下加个标记文件"）→ prompt 层拒绝
3. PM 调度 QA 诊断 → 调度 prompt 中包含 prod 路径与只读约束

验证完成后清理 fixture 与测试 issue。
