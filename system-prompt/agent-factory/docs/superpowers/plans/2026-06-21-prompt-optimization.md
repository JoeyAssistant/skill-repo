# Prompt Optimization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Optimize 5 agent-factory prompt files to delete doc-changes and doc/frontend/ mechanisms, strengthen data-schema field necessity, and enforce commit on all task types.

**Architecture:** Per-Issue task decomposition. Each task implements one spec decision end-to-end across all affected files. Final task verifies cross-file consistency.

**Tech Stack:** Markdown prompt files (no code/tests); grep + Read for verification.

**Spec reference:** `system-prompt/agent-factory/docs/superpowers/specs/2026-06-21-prompt-optimization-design.md`

---

## File Structure

5 files modified, 0 created:

| File | Issues touched |
|------|----------------|
| `system-prompt/agent-factory/designer.md` | 1, 2, 3 |
| `system-prompt/agent-factory/developer.md` | 1, 2, 4 |
| `system-prompt/agent-factory/agent-pm.md` | 1, 4 |
| `system-prompt/agent-factory/qa.md` | 2 |
| `system-prompt/agent-factory/spec-compliance.md` | 2, 3 |

All paths below are relative to repo root `/Users/zhuowentao/Workspace/repos/JoeyAssistant/skill-repo/`.

---

## Task 1: Issue 1 — 删除 doc-changes 机制

**Files:**
- Modify: `system-prompt/agent-factory/designer.md`
- Modify: `system-prompt/agent-factory/agent-pm.md`
- Modify: `system-prompt/agent-factory/developer.md`

**Scope:** 完全删除 `doc-changes/` 目录机制和 diff 生成/应用流程。保留 DESIGN.md `## Doc 变更清单` 章节为纯文本概要。

### designer.md 修改

- [ ] **Step 1: 删除 Feature Management 目录结构中的 doc-changes/**

File: `system-prompt/agent-factory/designer.md`

old_string:
```
{Root}/.features/
  index.md                          # 需求索引
  <NNN>-<feature-name>/
    REQUIREMENTS.md                 # 需求讨论结论（PM 创建，Designer 读取）
    DESIGN.md                       # 设计文档（从模板生成）
    doc-changes/                    # doc 变更 diff 文件
      <filename>.diff
```

new_string:
```
{Root}/.features/
  index.md                          # 需求索引
  <NNN>-<feature-name>/
    REQUIREMENTS.md                 # 需求讨论结论（PM 创建，Designer 读取）
    DESIGN.md                       # 设计文档（从模板生成）
```

- [ ] **Step 2: 更新 approved 状态触发条件**

File: `system-prompt/agent-factory/designer.md`

old_string:
```
| approved | 设计通过 review，diff 通过审阅，待开发 | 所有 doc-changes/*.diff 审阅通过 |
```

new_string:
```
| approved | 设计通过 review，待开发 | DESIGN.md review 通过 |
```

- [ ] **Step 3: 删除职责边界操作范围中的 doc-changes 项**

File: `system-prompt/agent-factory/designer.md`

old_string:
```
**designer 操作范围**：
- `{Root}/.features/` 下的所有文件（index.md、DESIGN.md、doc-changes/*.diff）
- `doc/<module>/` 下的 schema 和 persistence 文件
```

new_string:
```
**designer 操作范围**：
- `{Root}/.features/` 下的所有文件（index.md、DESIGN.md）
- `doc/<module>/` 下的 schema 和 persistence 文件
```

- [ ] **Step 4: 删除工作流 step 6 "生成 diff"，重编号 step 7 → 6**

File: `system-prompt/agent-factory/designer.md`

old_string:
```
5. **Review 设计文档**：将 spec-compliance 返回的 fail 项作为 review suggestions，使用 doc-review skill 对 DESIGN.md / doc 文件进行 review，直至确认完成
6. **生成 diff**：读取当前 `{Root}/doc/` 下所有 `.md` 文件（不含 `doc/frontend/` 目录），基于 DESIGN.md 内容为涉及变更的文件生成 `doc-changes/*.diff`（unified diff 格式）
7. **返回结果**：将结构化结果返回给 PM
```

new_string:
```
5. **Review 设计文档**：将 spec-compliance 返回的 fail 项作为 review suggestions，使用 doc-review skill 对 DESIGN.md / doc 文件进行 review，直至确认完成
6. **返回结果**：将结构化结果返回给 PM
```

- [ ] **Step 5: 删除 ### diff 文件规范 整章**

File: `system-prompt/agent-factory/designer.md`

old_string:
```

### diff 文件规范

- 格式：标准 unified diff（`--- a/{Root}/doc/xxx.md` / `+++ b/{Root}/doc/xxx.md` / `@@ hunk @@`）
- 基于 doc 文件当前内容生成，确保上下文行准确
- 每个 doc 文件一个 `.diff` 文件，放在 `doc-changes/` 目录下
- diff 只包含变更部分，不包含无关行
- 覆盖范围：`{Root}/doc/` 下所有 `.md` 文件（不含 `doc/frontend/` 目录），仅对本次需求涉及变更的文件生成 diff

## 设计文档输出规范
```

new_string:
```

## 设计文档输出规范
```

- [ ] **Step 6: 更新 DESIGN.md 模板的 `## Doc 变更清单` 章节为文本概要**

File: `system-prompt/agent-factory/designer.md`

old_string:
```
## Doc 变更清单
<!-- 列出受影响的 doc 文件及变更类型 -->
```

new_string:
```
## Doc 变更清单
<!-- 列出受影响的 doc 文件及变更类型（纯文本，不生成 diff） -->
<!-- 示例：
- doc/financial/data-schema.md（新增 IncomeRecord dataclass）
- doc/financial/data-persistence.md（修改存储路径）
- doc/common/data-schema.md（无变更）
-->
```

- [ ] **Step 7: 更新输出格式 JSON 的 artifacts 字段**

File: `system-prompt/agent-factory/designer.md`

old_string:
```
  "status": "complete",
  "feature_number": "<NNN>",
  "artifacts": ["DESIGN.md", "doc-changes/<filename>.diff"],
  "summary": "<简要描述设计内容>",
```

new_string:
```
  "status": "complete",
  "feature_number": "<NNN>",
  "artifacts": ["DESIGN.md", "doc/<module>/data-schema.md", "doc/<module>/data-persistence.md"],
  "summary": "<简要描述设计内容>",
```

### agent-pm.md 修改

- [ ] **Step 8: 删除 Feature 目录结构中的 doc-changes/**

File: `system-prompt/agent-factory/agent-pm.md`

old_string:
```
.features/
  index.md                          # 需求索引
  <NNN>-<feature-name>/
    REQUIREMENTS.md                 # 需求讨论结论（draft 阶段创建）
    DESIGN.md                       # 设计文档
    doc-changes/                    # doc 变更 diff 文件
      <filename>.diff
    BLOCKED.md                      # 阻塞记录（blocked 时创建）
    POC-REPORT.md                   # 技术可行性评估报告（tech-feasibility blocked 时生成）
```

new_string:
```
.features/
  index.md                          # 需求索引
  <NNN>-<feature-name>/
    REQUIREMENTS.md                 # 需求讨论结论（draft 阶段创建）
    DESIGN.md                       # 设计文档
    BLOCKED.md                      # 阻塞记录（blocked 时创建）
    POC-REPORT.md                   # 技术可行性评估报告（tech-feasibility blocked 时生成）
```

- [ ] **Step 9: 更新 approved 状态触发条件**

File: `system-prompt/agent-factory/agent-pm.md`

old_string:
```
| approved | 设计通过 review，diff 通过审阅，待开发 | 用户终审通过 |
```

new_string:
```
| approved | 设计通过 review，待开发 | 用户终审通过 |
```

- [ ] **Step 10: 删除调度 designer 指令中 step 7 "Generate doc-changes"**

File: `system-prompt/agent-factory/agent-pm.md`

old_string:
```
## Instructions
1. Read REQUIREMENTS.md, especially Agent Type, Deploy Mode, and Feature Type
2. Update index.md status to "designing"
3. If module boundary changes are involved: write module boundary proposal in DESIGN.md, submit to user via PM for confirmation
3a. If Feature Type = migration: follow Migration Feature 设计规范（扫描现有 cli/*.py，设计 src/<module>/ 拆分方案，跳过新功能设计）
4. Create DESIGN.md following the template (select artifacts per Agent Type)
5. Run spec-compliance check
6. Use doc-review skill to refine
7. Generate doc-changes/*.diff
8. Return structured result
```

new_string:
```
## Instructions
1. Read REQUIREMENTS.md, especially Agent Type, Deploy Mode, and Feature Type
2. Update index.md status to "designing"
3. If module boundary changes are involved: write module boundary proposal in DESIGN.md, submit to user via PM for confirmation
3a. If Feature Type = migration: follow Migration Feature 设计规范（扫描现有 cli/*.py，设计 src/<module>/ 拆分方案，跳过新功能设计）
4. Create DESIGN.md following the template (select artifacts per Agent Type)
5. Run spec-compliance check
6. Use doc-review skill to refine
7. Return structured result
```

- [ ] **Step 11: 删除调度 developer 指令中 step 2 "Apply doc-changes"**

File: `system-prompt/agent-factory/agent-pm.md`

old_string:
```
## Instructions
1. Read DESIGN.md
2. Apply doc-changes/*.diff to doc/ files
3. Update index.md status to "implementing"
4. Implement all code per design (按 Agent Type 选 artifact)
5. Run tests
6. Git commit (one feature = one commit; migration feature 用 refactor(migrate): 前缀)
7. On success: update index.md status to "qa-reviewing", return complete
8. On blocker: update index.md status to "blocked", return blocked with reason
```

new_string:
```
## Instructions
1. Read DESIGN.md
2. Update index.md status to "implementing"
3. Implement all code per design (按 Agent Type 选 artifact)
4. Run tests
5. Git commit (one feature = one commit; migration feature 用 refactor(migrate): 前缀)
6. On success: update index.md status to "qa-reviewing", return complete
7. On blocker: update index.md status to "blocked", return blocked with reason
```

- [ ] **Step 12: 更新 PM Review 标准中的 doc-changes 引用**

File: `system-prompt/agent-factory/agent-pm.md`

old_string:
```
- **需求覆盖率**：DESIGN.md 是否覆盖了 requirement brief 中的每个功能点
- **完整性**：DESIGN.md 各章节是否完整填写（概述、数据结构、CLI 命令、持久化、模块关系、doc 变更清单）
- **一致性**：doc-changes 涉及的文件范围是否与需求范围匹配
```

new_string:
```
- **需求覆盖率**：DESIGN.md 是否覆盖了 requirement brief 中的每个功能点
- **完整性**：DESIGN.md 各章节是否完整填写（概述、数据结构、CLI 命令、持久化、模块关系、Doc 变更清单）
- **一致性**：DESIGN.md Doc 变更清单 章节涉及的文件范围是否与需求范围匹配
```

- [ ] **Step 13: 更新 PM Review 后展示内容**

File: `system-prompt/agent-factory/agent-pm.md`

old_string:
```
PM 将设计提交用户终审：
- 展示 DESIGN.md 概要和 doc-changes/*.diff
- 使用 doc-review skill（如已安装）进行交互式 review
- 用户确认后，更新 status=approved
```

new_string:
```
PM 将设计提交用户终审：
- 展示 DESIGN.md 概要和 git diff 摘要（`git diff --stat doc/`）
- 使用 doc-review skill（如已安装）进行交互式 review
- 用户确认后，更新 status=approved
```

### developer.md 修改

- [ ] **Step 14: 删除常规开发任务 Instructions 中 step 2 "Apply doc-changes"**

File: `system-prompt/agent-factory/developer.md`

old_string:
```
## Instructions
1. Read DESIGN.md
2. Apply doc-changes/*.diff to doc/ files
3. Update index.md status to "implementing"
4. Implement all code per design (按 Agent Type 选 artifact)
5. Run tests
6. Git commit (one feature = one commit, see Git 提交规范)
   - Migration feature commit message 用 `refactor(migrate):` 前缀
7. On success: update index.md status to "qa-reviewing", return complete
8. On blocker: update index.md status to "blocked", return blocked with reason
```

new_string:
```
## Instructions
1. Read DESIGN.md
2. Update index.md status to "implementing"
3. Implement all code per design (按 Agent Type 选 artifact)
4. Run tests
5. Git commit (one feature = one commit, see Git 提交规范)
   - Migration feature commit message 用 `refactor(migrate):` 前缀
6. On success: update index.md status to "qa-reviewing", return complete
7. On blocker: update index.md status to "blocked", return blocked with reason
```

- [ ] **Step 15: 删除开发前准备 step 1 阅读列表中的 doc-changes 行**

File: `system-prompt/agent-factory/developer.md`

old_string:
```
1. **阅读设计文档**：按以下顺序阅读设计文档
   - `{Root}/.features/<NNN>-<name>/DESIGN.md` → 理解需求设计（先读这个，特别是 Agent Type）
   - `{Root}/.features/<NNN>-<name>/doc-changes/*.diff` → 理解 doc 文件需要做哪些变更
   - **各 module 设计文档**（从 DESIGN.md「各 Module 设计」章节确定涉及哪些 module）：
```

new_string:
```
1. **阅读设计文档**：按以下顺序阅读设计文档
   - `{Root}/.features/<NNN>-<name>/DESIGN.md` → 理解需求设计（先读这个，特别是 Agent Type）
   - **各 module 设计文档**（从 DESIGN.md「各 Module 设计」章节确定涉及哪些 module）：
```

- [ ] **Step 16: 删除开发前准备 step 2 "应用 doc 变更"**

File: `system-prompt/agent-factory/developer.md`

old_string:
```
2. **应用 doc 变更**：将 `{Root}/.features/<NNN>-<name>/doc-changes/*.diff` 逐个应用到对应的 `{Root}/doc/` 文件。这是编码前的必要步骤，确保 `{Root}/doc/` 文档与设计一致后再开始编码
3. **确认理解**：如果设计文档中存在模糊或矛盾之处，返回 blocked 给 PM，由 PM 协调解决
4. **遵循设计**：严格按照设计文档（含已更新的 `{Root}/doc/` 文件）实现，不自行更改架构或数据结构定义
5. **更新状态**：开始编码前，将 `{Root}/.features/index.md` 中对应需求状态更新为 `implementing`；开发完成后更新为 `done`
6. **代码目录结构**（按 Agent Type）：
```

new_string:
```
2. **确认理解**：如果设计文档中存在模糊或矛盾之处，返回 blocked 给 PM，由 PM 协调解决
3. **遵循设计**：严格按照设计文档（含 `{Root}/doc/` 文件）实现，不自行更改架构或数据结构定义
4. **更新状态**：开始编码前，将 `{Root}/.features/index.md` 中对应需求状态更新为 `implementing`；开发完成后更新为 `done`
5. **代码目录结构**（按 Agent Type）：
```

### 验证 + Commit

- [ ] **Step 17: 验证 doc-changes 已完全清除**

Run:
```bash
grep -n "doc-changes" system-prompt/agent-factory/*.md
```
Expected: 0 hits（"Doc 变更清单" 不算，那是 DESIGN.md 模板章节名，不含连字符的 "doc-changes"）

- [ ] **Step 18: 验证 "Apply doc-changes" / "Generate doc-changes" 已清除**

Run:
```bash
grep -nE "Apply doc-changes|Generate doc-changes|生成 diff|diff 文件规范" system-prompt/agent-factory/*.md
```
Expected: 0 hits

- [ ] **Step 19: Commit**

```bash
git add system-prompt/agent-factory/designer.md system-prompt/agent-factory/agent-pm.md system-prompt/agent-factory/developer.md
git commit -m "$(cat <<'EOF'
refactor: remove doc-changes mechanism from agent-factory prompts

doc-changes/*.diff was redundant: designer already writes doc/<module>/*.md
directly, and review uses git diff. Removes 14 references across 3 files.
DESIGN.md Doc 变更清单 chapter kept as text-only summary.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

## Task 2: Issue 2 — 删除 doc/frontend/ 机制

**Files:**
- Modify: `system-prompt/agent-factory/designer.md`
- Modify: `system-prompt/agent-factory/developer.md`
- Modify: `system-prompt/agent-factory/qa.md`
- Modify: `system-prompt/agent-factory/spec-compliance.md`

**Scope:** 删除 `doc/frontend/` HTML 预览机制。UI 设计下沉到 DESIGN.md `## Frontend` 章节（页面清单 + 关键交互 + API 对应表）。

### designer.md 修改

- [ ] **Step 1: 删除设计文档输出规范中的 doc/frontend/ 行**

File: `system-prompt/agent-factory/designer.md`

old_string:
```
| `{Root}/doc/mcp-server.md` | MCP tools 清单 + 部署模式 + 调用流程 | mcp-server |
| `{Root}/doc/frontend/` | 各页面 UI 预览 HTML 文件 | http-web |
```

new_string:
```
| `{Root}/doc/mcp-server.md` | MCP tools 清单 + 部署模式 + 调用流程 | mcp-server |
```

- [ ] **Step 2: 删除 ## Web UI 设计 整章**

File: `system-prompt/agent-factory/designer.md`

old_string:
```
## Web UI 设计

### 设计与开发流程
#### 设计先行，所见即所得
- `{Root}/doc/frontend/` 目录下，针对每一个网页，创建对应 UI 预览 `html` 文件，用于与用户讨论、修改、确认 UI 设计规格，使用 mock 数据
- **字体策略**：优先使用思源黑体 (Noto Sans SC) + 系统字体 fallback， 通过`@import url('https://cdn.bootcdn.net/ajax/libs/font-awesome/6.4.0/css/all.min.css')`加载（仅作增强，失败不影响页面显示）
- 每次修改后使用 `playwright` 验证 UI 预览是否符合设计规格

## 代码目录结构
```

new_string:
```
## 代码目录结构
```

- [ ] **Step 3: 删除 artifact 矩阵中的 doc/frontend/ 行**

File: `system-prompt/agent-factory/designer.md`

old_string:
```
| `doc/backend.md` | ✗ | ✓ | ✓ | ✗ |
| `doc/frontend/` | ✗ | ✗ | ✓ | ✗ |
| `mcp-server/` | ✗ | ✗ | ✗ | ✓ |
```

new_string:
```
| `doc/backend.md` | ✗ | ✓ | ✓ | ✗ |
| `mcp-server/` | ✗ | ✗ | ✗ | ✓ |
```

- [ ] **Step 4: 删除 http-web 目录结构示例中的 doc/frontend/**

File: `system-prompt/agent-factory/designer.md`

old_string:
```
    common/
      data-schema.md
    backend.md
    frontend/
      index.html
      ...
  script/                   # start.sh / stop.sh / status.sh
  test/
```

new_string:
```
    common/
      data-schema.md
    backend.md
  script/                   # start.sh / stop.sh / status.sh
  test/
```

- [ ] **Step 5: 扩展 DESIGN.md 模板的 ## Frontend 章节为三段结构**

File: `system-prompt/agent-factory/designer.md`

old_string:
```
## Frontend（仅 http-web）
<!-- 页面清单、关键交互 -->
```

new_string:
```
## Frontend（仅 http-web）

### 页面清单
<!-- 列出所有页面：路径、文件名、用途 -->

### 关键交互
<!-- 每个页面的关键用户操作流程 -->

### API 对应
| 页面 | 调用的 backend API |
|------|-------------------|
| <page> | <API list> |
```

### developer.md 修改

- [ ] **Step 6: 删除开发前准备阅读列表中的 doc/frontend/ 行**

File: `system-prompt/agent-factory/developer.md`

old_string:
```
     - `http-api` / `http-web`：`{Root}/doc/backend.md` → 后端 API 设计
     - `mcp-server`：`{Root}/doc/mcp-server.md` → MCP tools 设计
   - `{Root}/doc/frontend/` → UI 设计规格（仅 http-web 形态）
```

new_string:
```
     - `http-api` / `http-web`：`{Root}/doc/backend.md` → 后端 API 设计
     - `mcp-server`：`{Root}/doc/mcp-server.md` → MCP tools 设计
   - `{Root}/.features/<NNN>-<name>/DESIGN.md` → Frontend 章节（仅 http-web 形态）
```

### qa.md 修改

- [ ] **Step 7: 更新 UI 元素验收行，改指 DESIGN.md Frontend 章节**

File: `system-prompt/agent-factory/qa.md`

old_string:
```
| UI 元素 | ✗ | ✗ | ✓ `doc/frontend/` | ✗ |
```

new_string:
```
| UI 元素 | ✗ | ✗ | ✓ DESIGN.md `## Frontend` 章节 | ✗ |
```

### spec-compliance.md 修改

- [ ] **Step 8: 更新 F 检查组标题和检查项，改指 DESIGN.md Frontend 章节**

File: `system-prompt/agent-factory/spec-compliance.md`

old_string:
```
### F - doc/frontend/（仅 http-web，新增）

| # | Check | Requirement | Pass Criteria |
|---|-------|-------------|---------------|
| F1 | 页面清单 | 列出所有页面 html 文件 | `doc/frontend/` 下每个 .html 都列入清单 |
| F2 | 关键交互描述 | 每个页面的关键交互流程 | 每个页面有交互流程说明 |
| F3 | API 对应关系 | 每个页面映射到 backend 的哪些 API | 页面与 API 调用关系清晰 |
```

new_string:
```
### F - DESIGN.md Frontend 章节（仅 http-web）

| # | Check | Requirement | Pass Criteria |
|---|-------|-------------|---------------|
| F1 | 页面清单 | DESIGN.md `## Frontend > ### 页面清单` 列出所有页面 | 每个页面有路径、文件名、用途 |
| F2 | 关键交互描述 | `### 关键交互` 章节描述每个页面的关键操作流程 | 每个页面有交互流程说明 |
| F3 | API 对应关系 | `### API 对应` 表格映射每个页面到 backend API | 页面与 API 调用关系清晰 |
```

- [ ] **Step 9: 更新输出 JSON 示例中的 doc/frontend/ 引用**

File: `system-prompt/agent-factory/spec-compliance.md`

old_string:
```
    {
      "file": "doc/frontend/",
      "summary": { "totalChecks": 3, "passed": ["F1","F3"], "failed": ["F2"] },
      "violations": [
        {
          "checkId": "F2",
          "check": "关键交互描述",
          "lineRange": null,
          "detail": "index.html 缺少关键交互流程描述"
        }
      ]
    }
```

new_string:
```
    {
      "file": "DESIGN.md (Frontend section)",
      "summary": { "totalChecks": 3, "passed": ["F1","F3"], "failed": ["F2"] },
      "violations": [
        {
          "checkId": "F2",
          "check": "关键交互描述",
          "lineRange": null,
          "detail": "DESIGN.md Frontend 章节缺少 ### 关键交互 子节"
        }
      ]
    }
```

### 验证 + Commit

- [ ] **Step 10: 验证 doc/frontend/ 已完全清除**

Run:
```bash
grep -nE "doc/frontend/|UI 预览|所见即所得" system-prompt/agent-factory/*.md
```
Expected: 0 hits

- [ ] **Step 11: Commit**

```bash
git add system-prompt/agent-factory/designer.md system-prompt/agent-factory/developer.md system-prompt/agent-factory/qa.md system-prompt/agent-factory/spec-compliance.md
git commit -m "$(cat <<'EOF'
refactor: remove doc/frontend/ preview, move UI specs to DESIGN.md

HTML preview maintenance cost was high and previews diverged from real
implementation. UI specs (page list + interactions + API mapping) now live
in DESIGN.md ## Frontend section. Updates F-group checks in spec-compliance
to reference DESIGN.md instead of doc/frontend/ directory.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

## Task 3: Issue 3 — data-schema 字段必要性原则

**Files:**
- Modify: `system-prompt/agent-factory/designer.md`
- Modify: `system-prompt/agent-factory/spec-compliance.md`

**Scope:** 用正向指令 + 消费方清单 + 2 行判断表替代负向约束。designer.md 重写 `## Data Schema` 章节，DESIGN.md 模板 Module 数据结构加消费方要求，spec-compliance.md 新增 S8/S9 检查。

### designer.md 修改

- [ ] **Step 1: 重写 ## Data Schema 整章**

File: `system-prompt/agent-factory/designer.md`

old_string:
```
## Data Schema
### 设计文档`{Root}/doc/<module>/data-schema.md`（按 module 拆分，跨 module 共享部分写在 `{Root}/doc/common/data-schema.md`）
**文件内容**
- 结合业务场景、功能，使用合理数据类型，定义简洁、清晰的数据结构
- 每个数据结构使用 `python dataclass` 定义，以及class与每个field相应文字描述

**dos**
- 字段值存在有限集合时，优先使用枚举（Python `enum`）而非字符串常量或整数魔法值
- 数据结构命名清晰、合理，保证一致性

**don'ts**
- 避免过度设计，定义agent功能非必要的数据结构以及字段，如不确定请于用户确认
- 文档仅承载数据结构定义，不体现业务使用代码或持久化等其他内容

### 关键原则
- **每个 module 的 `data-schema.md` 作为该 module 数据结构的唯一真值，必须保证跨文档一致性**
- **跨 module 共享数据结构以 `{Root}/doc/common/data-schema.md` 为唯一真值**
- 任何 data-schema 修改需先与用户讨论
```

new_string:
```
## Data Schema

设计文档 `{Root}/doc/<module>/data-schema.md`（按 module 拆分，跨 module 共享部分写在 `{Root}/doc/common/data-schema.md`）

### 文件内容

- 结合业务场景、功能，使用合理数据类型，定义简洁、清晰的数据结构
- 每个数据结构使用 `python dataclass` 定义，class 与每个 field 配文字描述

### 字段必要性原则（核心）

每个字段必须能回答"谁在什么时候读取这个字段？"。设计 dataclass 前先做两件事：

1. **列出消费方清单**：该数据结构被哪些场景使用？
   - CLI 命令 / API 端点 / UI 元素 / 日志读取 / 持久化反序列化
2. **逐字段归因**：每个字段属于哪个消费方？没有明确消费方的不写入 schema

**判断标准（写入字段前自查）**：

| 场景 | 处理 |
|------|------|
| 字段有明确消费方（CLI/API/UI/日志读取它） | 保留 |
| 字段"将来可能用到"或"看起来应该有" | 不保留（YAGNI） |

**dos**

- 字段值存在有限集合时，优先使用枚举（Python `enum`）而非字符串常量或整数魔法值
- 数据结构命名清晰、合理，保证一致性
- 文档仅承载数据结构定义，不体现业务使用代码或持久化等其他内容

### 关键原则

- **每个 module 的 `data-schema.md` 作为该 module 数据结构的唯一真值，必须保证跨文档一致性**
- **跨 module 共享数据结构以 `{Root}/doc/common/data-schema.md` 为唯一真值**
- 任何 data-schema 修改需先与用户讨论
```

- [ ] **Step 2: 更新 DESIGN.md 模板 Module 数据结构章节，加消费方清单要求**

File: `system-prompt/agent-factory/designer.md`

old_string:
```
### <Module-A>
#### 数据结构
<!-- 引用 doc/<module-A>/data-schema.md，列关键 entity -->
#### 持久化
```

new_string:
```
### <Module-A>
#### 数据结构
<!-- 引用 doc/<module-A>/data-schema.md，列关键 entity -->
<!-- 每个 dataclass 附消费方清单（被哪些 CLI/API/UI/日志使用） -->
#### 持久化
```

### spec-compliance.md 修改

- [ ] **Step 3: 在 S 组新增 S8 / S9 检查项**

File: `system-prompt/agent-factory/spec-compliance.md`

old_string:
```
| S6 | 纯数据结构 | 不包含业务逻辑代码或持久化内容 | 仅定义数据结构，不包含函数、方法、存储逻辑 |
| S7 | 唯一真值声明 | 文档说明其作为数据结构唯一真值的地位 | 文档中声明跨文档一致性要求 |
```

new_string:
```
| S6 | 纯数据结构 | 不包含业务逻辑代码或持久化内容 | 仅定义数据结构，不包含函数、方法、存储逻辑 |
| S7 | 唯一真值声明 | 文档说明其作为数据结构唯一真值的地位 | 文档中声明跨文档一致性要求 |
| S8 | 字段消费方标注 | DESIGN.md 中每个 dataclass 附消费方清单 | DESIGN.md「各 Module 设计 > 数据结构」章节中，每个 dataclass 列出消费方（CLI/API/UI/日志） |
| S9 | 字段必要性自检 | data-schema.md 中无"将来可能"/"看起来应该有"类描述 | 字段描述不包含"将来可能用到"、"看起来应该有"、"预留"等启发式关键词；发现疑似项列入 violation 待 designer 复核 |
```

- [ ] **Step 4: 更新 S5 措辞与新的字段必要性原则对齐**

File: `system-prompt/agent-factory/spec-compliance.md`

old_string:
```
| S5 | 无过度设计 | 不包含非必要的字段和结构 | 每个字段都能对应到实际功能需求 |
```

new_string:
```
| S5 | 无过度设计 | 不包含非必要的字段和结构 | 每个字段都能对应到明确的消费方（CLI/API/UI/日志/持久化反序列化）；与 S8/S9 协同检查 |
```

- [ ] **Step 5: 更新输出 JSON 示例中 S 组的 totalChecks（7 → 9）**

File: `system-prompt/agent-factory/spec-compliance.md`

old_string:
```
    {
      "file": "doc/financial/data-schema.md",
      "summary": { "totalChecks": 7, "passed": ["S1","S2","S4","S5","S6","S7"], "failed": ["S3"] },
```

new_string:
```
    {
      "file": "doc/financial/data-schema.md",
      "summary": { "totalChecks": 9, "passed": ["S1","S2","S4","S5","S6","S7","S8"], "failed": ["S3","S9"] },
```

- [ ] **Step 6: 同步更新 doc/common/data-schema.md 示例的 totalChecks**

File: `system-prompt/agent-factory/spec-compliance.md`

old_string:
```
    {
      "file": "doc/common/data-schema.md",
      "summary": { "totalChecks": 7, "passed": ["S1","S2","S3","S4","S5","S6","S7"], "failed": [] },
      "violations": []
    },
```

new_string:
```
    {
      "file": "doc/common/data-schema.md",
      "summary": { "totalChecks": 9, "passed": ["S1","S2","S3","S4","S5","S6","S7","S8","S9"], "failed": [] },
      "violations": []
    },
```

### 验证 + Commit

- [ ] **Step 7: 验证 don'ts 章节已删除**

Run:
```bash
grep -nE "避免过度设计|如不确定请于用户确认" system-prompt/agent-factory/designer.md
```
Expected: 0 hits

- [ ] **Step 8: 验证 S8/S9 已新增**

Run:
```bash
grep -nE "^\| S8 |^\| S9 " system-prompt/agent-factory/spec-compliance.md
```
Expected: 2 hits

- [ ] **Step 9: Commit**

```bash
git add system-prompt/agent-factory/designer.md system-prompt/agent-factory/spec-compliance.md
git commit -m "$(cat <<'EOF'
feat: strengthen data-schema field necessity with consumer-list principle

Replaces negative constraint ("避免过度设计...如不确定请于用户确认") with
positive instruction: every field must answer "who reads this field?".
Designer lists consumers per dataclass before designing fields; judgment
table filters YAGNI cases. spec-compliance adds S8 (consumer annotation)
and S9 (heuristic keyword scan) as backup enforcement.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

## Task 4: Issue 4 — commit 强制

**Files:**
- Modify: `system-prompt/agent-factory/developer.md`
- Modify: `system-prompt/agent-factory/agent-pm.md`

**Scope:** 重写 developer.md `## Git 提交规范`，移除 bug 修复例外；输出 JSON 加 `commit_sha` 必填；3 个任务 input format 加 commit step；PM 3 个 dispatch 指令加 commit step；commit message 全部不带 `(#<NNN>)`。

### developer.md 修改

- [ ] **Step 1: 重写 ## Git 提交规范 整章**

File: `system-prompt/agent-factory/developer.md`

old_string:
```
## Git 提交规范

### 提交时机

Developer 完成编码和测试后，必须执行 git commit，然后才返回 complete。

### 提交规则

- **一个 feature 对应一个 commit**：实现完一个 feature 的所有代码后，执行一次 git add + git commit
- QA 修复也同理：修复完所有 QA 问题时，执行一次 git add + git commit
- Bug 修复（issue）不要求自动提交，由 PM 决定提交策略

### Commit Message 格式

多项目模式：

```
feat(<project-id>): <feature title> (#<NNN>)

<DESIGN.md 概要，1-2 句>
```

```
fix(<project-id>): 修复 QA 发现的 <issue summary> (#<NNN>)

QA round N: <修复内容>
```

单项目模式（project-id 省略）：

```
feat: <feature title> (#<NNN>)

<DESIGN.md 概要，1-2 句>
```

### 不提交的情况

- 被 blocked 时（代码不完整）
- Bug 修复（issue 类型，由 PM 决定）
```

new_string:
```
## Git 提交规范

### 提交时机

代码修改完成后必须立即 commit，然后才返回 complete。

### 提交规则（无一例外）

所有代码修改完成后必须 commit：
- Feature 实现完成 → 1 个 commit
- QA 修复完成 → 1 个 commit
- Bug 修复（issue）完成 → 1 个 commit

### 唯一不 commit 的情况

- blocked（代码不完整）

### Commit 前自检

返回 complete 前，developer 必须执行 `git log -1 --oneline` 确认最新 commit 是本次任务的。若工作区仍有未提交的代码改动，禁止返回 complete。

### Commit Message 格式

Feature 实现（多项目模式）：

```
feat(<project-id>): <描述修改内容>

<DESIGN.md 概要，1-2 句>
```

Feature 实现（单项目模式）：

```
feat: <描述修改内容>

<DESIGN.md 概要，1-2 句>
```

QA 修复：

```
fix(<project-id>): 修复 QA 发现的 <问题描述>

QA round N: <修复内容>
```

Bug 修复（issue，多项目模式）：

```
fix(<project-id>): <问题描述>

<修复概要>
```

Bug 修复（issue，单项目模式）：

```
fix: <问题描述>

<修复概要>
```

Migration feature：

```
refactor(migrate): migrate <module> to new architecture

<迁移概要>
```
```

- [ ] **Step 2: 输出格式 JSON 新增 commit_sha 字段**

File: `system-prompt/agent-factory/developer.md`

old_string:
```
完成开发后，必须以以下 JSON 格式返回结果给 PM：

```json
{
  "status": "complete",
  "feature_number": "<NNN>",
  "artifacts": ["<list of created/modified files>"],
  "summary": "<简要描述实现了什么>",
  "blocked_reason": null
}
```
```

new_string:
```
完成开发后，必须以以下 JSON 格式返回结果给 PM：

```json
{
  "status": "complete",
  "feature_number": "<NNN>",
  "commit_sha": "<commit hash>",
  "artifacts": ["<list of created/modified files>"],
  "summary": "<简要描述实现了什么>",
  "blocked_reason": null
}
```

**`commit_sha` 必填**，缺失视为未完成。blocked 状态下 `commit_sha` 为 null。
```

- [ ] **Step 3: 常规开发任务 Instructions 去 (#<NNN>)，return complete 加 commit_sha**

File: `system-prompt/agent-factory/developer.md`

old_string:
```
## Instructions
1. Read DESIGN.md
2. Update index.md status to "implementing"
3. Implement all code per design (按 Agent Type 选 artifact)
4. Run tests
5. Git commit (one feature = one commit, see Git 提交规范)
   - Migration feature commit message 用 `refactor(migrate):` 前缀
6. On success: update index.md status to "qa-reviewing", return complete
7. On blocker: update index.md status to "blocked", return blocked with reason
```

new_string:
```
## Instructions
1. Read DESIGN.md
2. Update index.md status to "implementing"
3. Implement all code per design (按 Agent Type 选 artifact)
4. Run tests
5. Git commit (one feature = one commit, see Git 提交规范)
   - Migration feature commit message 用 `refactor(migrate):` 前缀
6. Self-verify: `git log -1 --oneline` 确认最新 commit 是本次任务的
7. On success: update index.md status to "qa-reviewing", return complete with commit_sha
8. On blocker: update index.md status to "blocked", return blocked with reason
```

- [ ] **Step 4: Bug 直接修复任务 Instructions 新增 commit step + commit_sha**

File: `system-prompt/agent-factory/developer.md`

old_string:
```
## Instructions
1. Reproduce and diagnose the bug
2. Apply minimal fix
3. Add regression test
4. Run full test suite
5. On success: update issue status to "closed", return complete
6. On blocker: update issue status to "blocked", return blocked with reason
```

new_string:
```
## Instructions
1. Reproduce and diagnose the bug
2. Apply minimal fix
3. Add regression test
4. Run full test suite
5. Git commit (one issue = one commit, message: fix(<project>): <问题描述> 或单项目 fix: <问题描述>)
6. Self-verify: `git log -1 --oneline` 确认最新 commit 是本次任务的
7. On success: update issue status to "closed", return complete with commit_sha
8. On blocker: update issue status to "blocked", return blocked with reason
```

- [ ] **Step 5: QA 修复任务 Instructions 新增 commit step + commit_sha**

File: `system-prompt/agent-factory/developer.md`

old_string:
```
## Instructions
1. Read QA-REPORT.md
2. Fix each issue listed in QA report
3. Add regression tests for each fix
4. Run full test suite
5. On success: update index.md status to "qa-reviewing", return complete
6. On blocker: update index.md status to "blocked", return blocked with reason
```

new_string:
```
## Instructions
1. Read QA-REPORT.md
2. Fix each issue listed in QA report
3. Add regression tests for each fix
4. Run full test suite
5. Git commit (one QA round = one commit, message: fix(<project>): 修复 QA 发现的 <问题描述>)
6. Self-verify: `git log -1 --oneline` 确认最新 commit 是本次任务的
7. On success: update index.md status to "qa-reviewing", return complete with commit_sha
8. On blocker: update index.md status to "blocked", return blocked with reason
```

### agent-pm.md 修改

- [ ] **Step 6: 调度 developer（常规开发）指令加 self-verify + commit_sha**

File: `system-prompt/agent-factory/agent-pm.md`

old_string:
```
## Instructions
1. Read DESIGN.md
2. Update index.md status to "implementing"
3. Implement all code per design (按 Agent Type 选 artifact)
4. Run tests
5. Git commit (one feature = one commit; migration feature 用 refactor(migrate): 前缀)
6. On success: update index.md status to "qa-reviewing", return complete
7. On blocker: update index.md status to "blocked", return blocked with reason
```

new_string:
```
## Instructions
1. Read DESIGN.md
2. Update index.md status to "implementing"
3. Implement all code per design (按 Agent Type 选 artifact)
4. Run tests
5. Git commit (one feature = one commit; migration feature 用 refactor(migrate): 前缀)
6. Self-verify: `git log -1 --oneline` 确认最新 commit 是本次任务的
7. On success: update index.md status to "qa-reviewing", return complete with commit_sha
8. On blocker: update index.md status to "blocked", return blocked with reason
```

- [ ] **Step 7: 调度 developer（Bug 直接修复）指令加 commit step + commit_sha**

File: `system-prompt/agent-factory/agent-pm.md`

old_string:
```
## Instructions
1. Update issue status to "triaging" in <Root>/.issues/index.md
2. Reproduce and diagnose the bug
3. Apply minimal fix
4. Add regression test
5. Run full test suite
6. On success: update issue status to "closed", return complete
7. On blocker: update issue status to "blocked", return blocked with reason
```

new_string:
```
## Instructions
1. Update issue status to "triaging" in <Root>/.issues/index.md
2. Reproduce and diagnose the bug
3. Apply minimal fix
4. Add regression test
5. Run full test suite
6. Git commit (one issue = one commit, message: fix(<project>): <问题描述> 或单项目 fix: <问题描述>)
7. Self-verify: `git log -1 --oneline` 确认最新 commit 是本次任务的
8. On success: update issue status to "closed", return complete with commit_sha
9. On blocker: update issue status to "blocked", return blocked with reason
```

- [ ] **Step 8: 调度 developer（QA 修复）指令加 commit step + commit_sha**

File: `system-prompt/agent-factory/agent-pm.md`

old_string:
```
## Instructions
1. Read QA-REPORT.md
2. Fix each issue listed in QA report
3. Add regression tests for each fix
4. Run full test suite
5. On success: update index.md status to "qa-reviewing", return complete
6. On blocker: update index.md status to "blocked", return blocked with reason
```

new_string:
```
## Instructions
1. Read QA-REPORT.md
2. Fix each issue listed in QA report
3. Add regression tests for each fix
4. Run full test suite
5. Git commit (one QA round = one commit, message: fix(<project>): 修复 QA 发现的 <问题描述>)
6. Self-verify: `git log -1 --oneline` 确认最新 commit 是本次任务的
7. On success: update index.md status to "qa-reviewing", return complete with commit_sha
8. On blocker: update index.md status to "blocked", return blocked with reason
```

- [ ] **Step 9: 调度 developer（QA 诊断后修复）指令加 commit step + commit_sha**

File: `system-prompt/agent-factory/agent-pm.md`

old_string:
```
## Instructions
1. Update issue status to "triaging" in <Root>/.issues/index.md
2. Read QA Diagnosis in NOTES.md
3. Apply fix based on QA's root cause analysis and suggestion
4. Add regression test
5. Run full test suite
6. On success: update issue status to "closed", return complete
7. On blocker: update issue status to "blocked", return blocked with reason
```

new_string:
```
## Instructions
1. Update issue status to "triaging" in <Root>/.issues/index.md
2. Read QA Diagnosis in NOTES.md
3. Apply fix based on QA's root cause analysis and suggestion
4. Add regression test
5. Run full test suite
6. Git commit (one issue = one commit, message: fix(<project>): <问题描述> 或单项目 fix: <问题描述>)
7. Self-verify: `git log -1 --oneline` 确认最新 commit 是本次任务的
8. On success: update issue status to "closed", return complete with commit_sha
9. On blocker: update issue status to "blocked", return blocked with reason
```

### 验证 + Commit

- [ ] **Step 10: 验证 "Bug 修复不要求自动提交" 例外已删除**

Run:
```bash
grep -nE "Bug 修复.*不要求自动提交|由 PM 决定提交策略" system-prompt/agent-factory/developer.md
```
Expected: 0 hits

- [ ] **Step 11: 验证 commit_sha 已加入 developer.md 输出 JSON**

Run:
```bash
grep -n "commit_sha" system-prompt/agent-factory/developer.md
```
Expected: ≥ 2 hits（JSON 示例 + 必填说明）

- [ ] **Step 12: 验证所有 developer 调度指令都有 commit step**

Run:
```bash
grep -nB1 "On success.*return complete with commit_sha" system-prompt/agent-factory/agent-pm.md
```
Expected: 4 hits（常规开发 + Bug 直接修复 + QA 修复 + QA 诊断后修复）

- [ ] **Step 13: Commit**

```bash
git add system-prompt/agent-factory/developer.md system-prompt/agent-factory/agent-pm.md
git commit -m "$(cat <<'EOF'
feat: enforce commit on all task types, add commit_sha to output

Removes "Bug 修复不要求自动提交" exception. All task types (feature / QA fix /
bug fix) now require commit before returning complete. Developer self-verifies
via git log -1 before status update. Output JSON adds mandatory commit_sha
field as contract. Commit messages no longer include (#NNN) per user pref.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

## Task 5: 跨文件一致性 review

**Files:**
- Read-only review: all 5 modified files

**Scope:** 全局检查 Task 1-4 修改后是否存在遗留引用、内部矛盾、跨文件不一致。这是最终质量门，发现问题就地修复。

- [ ] **Step 1: 全局搜索 doc-changes 残留**

Run:
```bash
grep -rn "doc-changes" system-prompt/agent-factory/*.md
```
Expected: 0 hits。如有残留，定位并删除。

- [ ] **Step 2: 全局搜索 doc/frontend/ 残留**

Run:
```bash
grep -rn "doc/frontend" system-prompt/agent-factory/*.md
```
Expected: 0 hits。如有残留，定位并删除或改指 DESIGN.md Frontend 章节。

- [ ] **Step 3: 验证 commit message 不带 (#<NNN>)**

Run:
```bash
grep -rnE "\(#[0-9]+\)|\(issue #[0-9]+\)" system-prompt/agent-factory/developer.md system-prompt/agent-factory/agent-pm.md
```
Expected: 0 hits（commit message 示例中不应出现编号引用）。如有残留，删除编号。

- [ ] **Step 4: 验证 4 个任务类型的 Instructions 都有 commit step**

Run:
```bash
grep -nB2 "Self-verify:.*git log" system-prompt/agent-factory/developer.md system-prompt/agent-factory/agent-pm.md
```
Expected: 在 developer.md 中 3 处（常规/Bug/QA 修复），在 agent-pm.md 中 4 处（常规/Bug 直接/QA 修复/QA 诊断后修复）。共 7 处。如不足，定位缺失的任务类型并补上。

- [ ] **Step 5: 验证 "return complete with commit_sha" 在所有 complete 路径**

Run:
```bash
grep -rn "return complete" system-prompt/agent-factory/developer.md system-prompt/agent-factory/agent-pm.md
```
Expected: 所有 developer 任务 complete 路径都带 `with commit_sha`。Bug 诊断（QA）的 complete 不带 commit_sha（QA 不 commit，只验收）。

- [ ] **Step 6: 验证 designer.md Data Schema 章节新结构完整**

Run:
```bash
grep -nE "字段必要性原则|消费方清单|判断标准" system-prompt/agent-factory/designer.md
```
Expected: ≥ 3 hits。验证章节标题、消费方清单 step、判断表都在。

- [ ] **Step 7: 验证 spec-compliance S 组检查项总数**

Run:
```bash
grep -cE "^\| S[0-9]+ \|" system-prompt/agent-factory/spec-compliance.md
```
Expected: 9（S1-S9）。如不是 9，定位 S 组表格。

- [ ] **Step 8: 验证 qa.md UI 元素验收行已改**

Run:
```bash
grep -n "UI 元素" system-prompt/agent-factory/qa.md
```
Expected: 1 hit，内容含 `DESIGN.md \`## Frontend\` 章节`，不含 `doc/frontend/`。

- [ ] **Step 9: 验证 DESIGN.md 模板 Doc 变更清单 + Frontend 双章节都更新**

Run:
```bash
grep -nE "## Doc 变更清单|## Frontend" system-prompt/agent-factory/designer.md
```
Expected: 2 hits。手动 Read 这两段，确认 Doc 变更清单 是文本概要（含示例注释），Frontend 是三段结构（页面清单/关键交互/API 对应）。

- [ ] **Step 10: Commit（如有 review 修复）**

如 Steps 1-9 发现任何问题并就地修复：

```bash
git add system-prompt/agent-factory/*.md
git commit -m "$(cat <<'EOF'
docs: cross-file consistency fixes for prompt optimization

Catches leftover doc-changes / doc/frontend references, missing commit
steps, or S-group count mismatches found in final consistency review.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

如无问题，跳过此 step。

---

## Self-Review Checklist

完成所有 task 后，确认：

- [ ] Task 1: `grep -rn "doc-changes" system-prompt/agent-factory/*.md` = 0 hits
- [ ] Task 2: `grep -rn "doc/frontend" system-prompt/agent-factory/*.md` = 0 hits
- [ ] Task 3: designer.md Data Schema 章节含 "字段必要性原则" + "消费方清单" + 2 行判断表
- [ ] Task 3: spec-compliance.md S 组有 S1-S9 共 9 项
- [ ] Task 4: developer.md 输出 JSON 含 `commit_sha`，必填说明存在
- [ ] Task 4: 所有 developer 任务 Instructions 都有 commit step 和 `return complete with commit_sha`
- [ ] Task 4: commit message 示例均无 `(#<NNN>)` 或 `(issue #<NNN>)`
- [ ] Task 5: 跨文件一致性 review 通过
