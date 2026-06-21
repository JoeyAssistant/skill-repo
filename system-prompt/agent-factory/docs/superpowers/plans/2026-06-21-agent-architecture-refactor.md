# Agent Architecture Refactor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 agent-factory 的 5 个 prompt 文件按设计文档（`docs/superpowers/specs/2026-06-21-agent-architecture-refactor-design.md`）落地为新架构：`src/<module>/` 中心化、Agent Type 四分法、强制迁移机制。

**Architecture:** 按文件分批修改，每个文件作为独立 task。修改顺序遵循依赖关系：先 `designer.md`（核心架构图和新 DESIGN.md 模板），再 `agent-pm.md`（流程和检测），然后 `developer.md` / `qa.md`（实现和验收），最后 `spec-compliance.md`（检查）。每个 task 内按修改点细分步骤，每步包含具体替换内容或对 spec 章节的精确引用。

**Tech Stack:** Markdown prompt files（agent-factory/system-prompt）

**Spec Reference:** `docs/superpowers/specs/2026-06-21-agent-architecture-refactor-design.md`（执行时打开此文档对照每个 step）

---

## File Structure

要修改的 5 个文件及其在新架构下的职责：

| 文件 | 行数 | 修改后职责 |
|------|------|------------|
| `designer.md` | 328 | 新架构图 + DESIGN.md 新模板 + 模块划分职责 + 共享数据提议流程 |
| `agent-pm.md` | 928 | REQUIREMENTS.md 新字段 + 旧结构检测 + migration feature 支持 |
| `developer.md` | 378 | 新目录结构 + 按 agent type 实现 + mcp-server 实现规范 |
| `qa.md` | 264 | 按 agent type 差异化验收（CLI/Backend/MCP/Frontend） |
| `spec-compliance.md` | 151 | 新检查清单（T/S/P/C/B/M/F 七组）+ 输入分发 + 多文件输出 |

不需要改：`poc.md`（跟形态无关）、`README.md`（后续单独更新）。

---

### Task 1: 更新 designer.md（核心架构 + DESIGN.md 模板）

**Files:**
- Modify: `system-prompt/agent-factory/designer.md`

按 spec 第 1 章（目录结构）、第 3 章（DESIGN.md 新模板）、第 5 章（共享数据新增流程）落地。

- [ ] **Step 1.1: 读现有 designer.md，定位各章节**

  Read `system-prompt/agent-factory/designer.md` 全文。记录以下章节的行号范围：
  - `## Agent参考架构`（mermaid 图）
  - `## Feature Management` → `### 目录结构`
  - `### DESIGN.md 模板`
  - `## 设计工作原则`
  - `## 工作流程`

- [ ] **Step 1.2: 替换 `## Agent参考架构` 章节的 mermaid 图**

  找到原 mermaid 图（`User ↔ WebUI ↔ Backend ↔ Agent ↔ CLI ↔ Data`），替换为反映新架构的 mermaid。

  **替换前的内容**（识别用）：
  ```mermaid
  graph TD
      User("👤 User")
      WebUI["Web UI(chat Bot)"]
      Claude["claude code"]
      Backend["Backend<br/>(FastAPI)"]
      Agent["Agent<br/>(Claude Agent SDK/Anthropic SDK)"]
      CLI["CLI<br/>(click)"]
      Data[("Data<br/>(JSON / database)")]

      User <--> WebUI
      User <--> Claude
      Claude <--> CLI
      WebUI <--> Backend
      Backend <--> Agent
      Backend <--> CLI
      Agent <--> CLI
      CLI <--> Data
  ```

  **替换后的内容**（反映 src/ 中心化，参考 spec §1）：
  ```mermaid
  graph TD
      User("👤 User")
      WebUI["Web UI<br/>(chat Bot)"]
      Claude["Claude Code<br/>(CLI 工具)"]
      Backend["Backend<br/>(FastAPI)"]
      Agent["Agent<br/>(SDK)"]
      McpServer["MCP Server<br/>(stdio/sse/http/mcpb)"]
      CLI["CLI Wrapper<br/>(click)"]
      SrcFinancial["src/financial/<br/>(service + models)"]
      SrcNews["src/news/<br/>(service + models)"]
      SrcCommon["src/common/<br/>(共享 models)"]
      Data[("Data<br/>(JSON / database)")]

      User <--> WebUI
      User <--> Claude
      WebUI <--> Backend
      Backend <--> Agent
      Backend --> SrcFinancial
      Backend --> SrcNews
      Agent --> SrcFinancial
      Agent --> SrcNews
      Claude <--> CLI
      CLI --> SrcFinancial
      CLI --> SrcNews
      Claude <--> McpServer
      McpServer --> SrcFinancial
      McpServer --> SrcNews
      SrcFinancial <--> Data
      SrcNews <--> Data
      SrcCommon -.-> SrcFinancial
      SrcCommon -.-> SrcNews
  ```

- [ ] **Step 1.3: 替换 `### 目录结构` 章节为四种形态**

  找到现有的 `### 目录结构`（包含 `.features/index.md` 等），在其下方保留 feature management 结构不变。

  找到 `## 代码目录结构` 章节（约 line 242-257），替换为 spec §1.1-1.4 的四种形态目录结构表 + 完整示意。完整内容见 spec §1（`#### 1.1 形态 cli-only 完整结构` 到 `#### 1.4 形态 mcp-server 完整结构`）。

  在四种形态结构前加一个表格（来自 spec §1 开头的 artifact 矩阵表）便于速查。

- [ ] **Step 1.4: 新增 `## Agent Type 与形态分流` 章节**

  在 `## 设计工作原则` 之后新增此章节。内容来自 spec §2 和 §D：

  ```markdown
  ## Agent Type 与形态分流

  Designer 接到任务时，第一步从 REQUIREMENTS.md 读取 `Agent Type`，按形态决定产出哪些 artifact。

  ### 四种形态

  | Agent Type | 描述 | 关键 artifact |
  |------------|------|---------------|
  | `cli-only` | 纯 CLI，给 Claude Code / nanobot 调用 | `src/` + `cli/<module>.py` + `doc/<module>/` |
  | `http-api` | HTTP API 服务，无前端 | `src/` + `backend/` + `doc/backend.md` |
  | `http-web` | HTTP 服务 + Web UI | `src/` + `backend/` + `doc/frontend/` + `doc/backend.md` |
  | `mcp-server` | MCP server，给 Claude Code 当工具 | `src/` + `mcp-server/` + `doc/mcp-server.md` |

  ### mcp-server 子模式（Deploy Mode）

  `mcp-server` 形态必须在 REQUIREMENTS.md 填 `Deploy Mode`：
  - `stdio`：Claude Code 启动本地进程，无鉴权，无 script/
  - `sse` / `http`：远程服务，需鉴权 + 部署脚本
  - `mcpb`：打包分发，需 `.mcpb` 文件结构

  ### 接入层取舍

  - `cli-only`：写 `cli/<module>.py`（click 脚本，调用 `src/<module>/service.py`）
  - `http-api` / `http-web`：写 `backend/`（FastAPI），**不写 CLI**
  - `mcp-server`：写 `mcp-server/`，**不写 CLI、不写 backend/**
  ```

- [ ] **Step 1.5: 替换 `### DESIGN.md 模板` 章节**

  找到现有 DESIGN.md 模板（约 line 125-147），整体替换为 spec §3 的新模板。

  完整新模板见 spec §3（从 `## Agent Type` 开始到 `## Doc 变更清单` 结束的整段 markdown）。

- [ ] **Step 1.6: 新增"模块划分建议"职责**

  在 `## 工作流程` 章节（约 line 153-162）的步骤 2「撰写设计」之前，新增步骤「模块划分建议」。

  ```markdown
  收到 PM 的设计任务后，按以下步骤执行：

  0. **读取 Agent Type**：从 REQUIREMENTS.md 读取 `Agent Type`（和 `Deploy Mode`），确定后续产出哪些 artifact
  1. **更新状态**：将 `{Root}/.features/index.md` 中对应需求状态更新为 `designing`
  2. **模块划分建议（涉及模块边界变化时）**：
     - 仅当本 feature 涉及新增 module、调整现有 module 边界时执行
     - 纯 module 内修改（加字段、加方法）跳过此步
     - 输出建议到 DESIGN.md「模块划分建议」章节：
       - 建议的 module 列表
       - 各 module 职责边界
       - 依赖关系（mermaid 图）
     - **用户决定，designer 给建议**：PM review 时拿给用户确认，designer 不自主拍板
  3. **撰写设计**：基于 REQUIREMENTS.md 和（如适用）确认后的模块划分，撰写 DESIGN.md
  ...（后续步骤不变，原 step 2-6 改为 step 3-7）
  ```

- [ ] **Step 1.7: 新增"共享数据提议"流程**

  在 `## 工作流程` 章节末尾或 `## 设计工作原则` 后新增：

  ```markdown
  ## 共享数据提议流程

  Designer 设计中如发现某数据结构（如 `AuditLog`）需要被 ≥2 个 module 使用，按以下流程提议加入 `doc/common/data-schema.md`：

  1. 在 DESIGN.md「模块划分建议」章节新增子节「提议 common 数据结构」：
     - 结构名、dataclass 字段定义
     - 使用方（≥2 module）
     - 理由（为什么不归属单一 module）
  2. PM 初步 review：合理性 + 是否真共享
  3. 用户在 DESIGN.md review 时确认
  4. 通过后 designer 写入 `doc/common/data-schema.md`
  5. 各 module 在 `data-schema.md` 中 import 引用，**不重复定义字段**

  详见 spec §5。
  ```

- [ ] **Step 1.8: 更新 `### 职责边界`**

  找到 `### 职责边界` 章节（约 line 149-151）。原文说 designer 仅操作 `.features/` 下文件，需要扩展说明：

  ```markdown
  ### 职责边界

  **designer 操作范围**：
  - `{Root}/.features/` 下的所有文件（index.md、DESIGN.md、doc-changes/*.diff）
  - `doc/<module>/` 下的 schema 和 persistence 文件
  - `doc/common/data-schema.md`（仅当用户确认新增/修改共享数据后）
  - `doc/backend.md` / `doc/mcp-server.md`（按 agent type）
  - `doc/frontend/`（仅 http-web）

  `{Root}/src/`、`{Root}/cli/`、`{Root}/backend/`、`{Root}/mcp-server/` 等代码目录由 developer 实现，designer 不直接修改。
  ```

- [ ] **Step 1.9: 读完整 designer.md 确认修改正确**

  Read 全文。验证：
  - 新 mermaid 图渲染正常（语法正确）
  - 四种形态目录结构完整（参考 spec §1.1-1.4）
  - DESIGN.md 新模板章节齐全（Agent Type / 模块划分建议 / 各 Module 设计 / 接入层设计 / Frontend / Doc 变更清单）
  - 共享数据提议流程章节存在
  - 章节顺序合理（Agent Type → 形态分流 → DESIGN 模板 → 工作流程 → 共享数据 → 职责边界）

- [ ] **Step 1.10: Commit**

  ```bash
  git add system-prompt/agent-factory/designer.md
  git commit -m "refactor(designer): apply new architecture (src/ + Agent Type + 模块划分)"
  ```

---

### Task 2: 更新 agent-pm.md（REQUIREMENTS.md + 旧结构检测 + migration feature）

**Files:**
- Modify: `system-prompt/agent-factory/agent-pm.md`

按 spec §2（REQUIREMENTS.md 新字段）、§6（强制迁移）落地。

- [ ] **Step 2.1: 读现有 agent-pm.md，定位各章节**

  Read 全文。记录以下章节的行号范围：
  - `### REQUIREMENTS.md 模板`
  - `## 模式检测`（PM 启动时的检测逻辑）
  - `## 日常巡检`
  - `## 任务调度`（各 subagent 调度 prompt 模板）
  - `### Issue 转 Feature 流程`

- [ ] **Step 2.2: 在 `### REQUIREMENTS.md 模板` 添加 Agent Type 字段**

  找到 `## Feature` 区块（含 ID、Name、Priority、Created 四个字段），新增两个字段：

  ```markdown
  ## Feature
  - **ID**: #<NNN>
  - **Name**: <kebab-case-name>
  - **Priority**: P1 | P2 | P3
  - **Created**: <YYYY-MM-DD>
  - **Agent Type**: cli-only | http-api | http-web | mcp-server
  - **Deploy Mode**: stdio | sse | http | mcpb    <!-- 仅 mcp-server 时填 -->
  ```

- [ ] **Step 2.3: 在 PM 工作模式中补充 Agent Type 讨论时机**

  找到 `#### 新需求讨论流程` 的 step 2（PM 引导讨论），在引导问题列表中追加：

  ```markdown
  2. PM 引导讨论（关注背景、价值、范围，不涉及技术细节）：
     - "为什么需要这个功能？"
     - "做成之后有什么好处？"
     - "具体要包含哪些内容？"
     - "这个 agent 怎么用？"（→ 确定 Agent Type）
       - 给 Claude Code 当工具 → `cli-only`
       - 提供 HTTP API → `http-api`
       - HTTP 服务 + 网页 → `http-web`
       - MCP 工具（暴露给 Claude Code）→ `mcp-server`
     - mcp-server 形态追加问："怎么部署？"（→ 确定 Deploy Mode: stdio/sse/http/mcpb）
     - 讨论中逐步将结论填入 REQUIREMENTS.md
  ```

- [ ] **Step 2.4: 在 `## 模式检测` 章节新增"旧结构检测"**

  找到现有的 `## 模式检测`（检测 `.workspace/` / `.features/`），在其后追加：

  ```markdown
  ### 项目结构新旧检测

  PM 启动时除检测工作模式外，还需检测项目结构是否过时：

  ```
  旧结构判定（满足任一）：
  1. 存在 doc/cli.md（单文件）
  2. 存在 doc/data-schema.md（单文件，未拆分到 doc/<module>/）
  ```

  **检测到旧结构时的行为**：

  | 用户动作 | PM 行为 |
  |----------|---------|
  | 启动 PM（日常巡检） | 标注"⚠️ 项目结构过时"，在状态总览顶部高亮提示 |
  | 查看现有 feature / issue | 允许（不阻塞读取） |
  | 提交新 issue | 允许接收，但提示"建议先发起迁移 feature" |
  | 新建 feature | 强制建议先迁移；用户坚持新建 → 允许，但 Designer 执行时若遇结构冲突 → blocked |
  | 发起迁移 feature | 走 migration feature 流程 |

  **核心原则**：PM 不硬阻塞用户操作，但通过持续提醒 + subagent 自动 blocked 让迁移成为"必须做的事"。

  详见 spec §6。
  ```

- [ ] **Step 2.5: 在 `## 日常巡检` 章节加入结构警告**

  找到 `## 日常巡检`（单项目模式 / 多项目模式），在汇报内容列表中加入：

  ```markdown
  - 是否存在"⚠️ 项目结构过时"警告（旧结构检测命中）
  ```

- [ ] **Step 2.6: 新增 `## Migration Feature 流程` 章节**

  在 `### Issue 转 Feature 流程` 之后新增（来自 spec §6.3）：

  ```markdown
  ## Migration Feature 流程

  存量项目迁移到新结构时，走标准 feature 流程，但有以下差异：

  ### 创建 migration feature

  PM 与用户讨论时必填两项：
  - **Agent Type**：用户决定迁完后的形态
  - **迁移范围**：全量 / 部分 module（建议全量）

  并在 `.features/index.md` 标记 `Type: migration`，便于识别。

  ### REQUIREMENTS.md 约束

  - **纯迁移，不改行为，不加功能**
  - 迁移过程中如发现 bug，记录到 `.issues/`，不在 migration feature 内修

  ### 执行流程

  ```
  用户: "把这个项目迁移到新结构"
    ↓
  PM 创建 migration feature（标记 Type: migration）
    ↓
  Designer 设计迁移方案：
    - 扫描现有 cli/*.py，推断 module 边界
    - 设计 src/<module>/ 拆分方案
    - 设计 doc/<module>/data-schema.md 拆分
    - 列出 doc/common/data-schema.md 候选
    - 用户确认方案
    ↓
  Developer 分批执行（按 module）：
    - 每个 module 迁移后跑全量测试，确认行为不变
    - 全部完成后删除旧文件（doc/cli.md、doc/data-schema.md 等）
    - git commit（一个迁移 feature = 一个 commit）
    ↓
  QA 验收：
    - 全量 E2E，确认功能与迁移前一致
    - 通过 → status=done
    - PM 下次巡检自动取消"项目结构过时"警告
  ```

  ### 失败兜底

  blocked → Designer 重新设计（拆得更细）→ 重试。反复失败（>3 轮）→ 升级用户决策。
  ```

- [ ] **Step 2.7: 更新 `## 任务调度` 中的 Designer 调度 prompt**

  找到 `### 调用 designer subagent`（约 line 534-559），更新 prompt 模板以体现新流程：

  ```markdown
  通过 Agent tool（`run_in_background: true`）调用 `designer` subagent，传入以下 prompt：

  ```
  ## Task
  设计 feature #<NNN>: <title>

  ## Project
  Name: <project-name>
  Root: <project-root-path>

  ## Agent Type
  <cli-only | http-api | http-web | mcp-server>
  <!-- mcp-server 时附加 -->
  ## Deploy Mode
  <stdio | sse | http | mcpb>

  ## Requirements
  Read `<Root>/.features/<NNN>-<name>/REQUIREMENTS.md` for full requirement details.

  ## Feature Directory
  <Root>/.features/<NNN>-<name>/

  ## Instructions
  1. Read REQUIREMENTS.md, especially Agent Type and Deploy Mode
  2. Update index.md status to "designing"
  3. If涉及模块边界变化: write 模块划分建议 section, submit to user via PM
  4. Create DESIGN.md following the template (按 Agent Type 选 artifact)
  5. Run spec-compliance check
  6. Use doc-review skill to refine
  7. Generate doc-changes/*.diff
  8. Return structured result
  ```
  ```

- [ ] **Step 2.8: 读完整 agent-pm.md 确认修改正确**

  Read 全文。验证：
  - REQUIREMENTS.md 模板含 Agent Type / Deploy Mode 字段
  - 新需求讨论流程含形态询问
  - 模式检测含旧结构检测
  - 日常巡检含结构警告
  - Migration Feature 流程章节存在且完整
  - Designer 调度 prompt 含 Agent Type 参数

- [ ] **Step 2.9: Commit**

  ```bash
  git add system-prompt/agent-factory/agent-pm.md
  git commit -m "refactor(pm): add Agent Type field, legacy structure detection, migration feature flow"
  ```

---

### Task 3: 更新 developer.md（新目录结构 + 按 Agent Type 实现）

**Files:**
- Modify: `system-prompt/agent-factory/developer.md`

按 spec §1（目录结构）、§C（形态 2 无 CLI）、§1.4（CLI 调用方式）落地。

- [ ] **Step 3.1: 读现有 developer.md，定位各章节**

  Read 全文。记录：
  - `## 开发前准备` → 步骤 6「代码目录结构」
  - `## 开发原则` → `### data-schema一致性`
  - 各任务输入格式（常规开发 / Bug 修复 / QA 修复）

- [ ] **Step 3.2: 替换代码目录结构**

  找到现有的代码目录结构（约 line 113-128），替换为：

  ```markdown
  6. **代码目录结构**（按 Agent Type）：

  **形态 cli-only**：
  ```
  {Root}/src/<module>/{__init__.py, service.py, models.py}
  {Root}/src/common/                # 共享数据（可选）
  {Root}/cli/<module>.py            # CLI wrapper
  {Root}/doc/<module>/{data-schema.md, data-persistence.md}
  {Root}/doc/common/                # 共享 schema（可选）
  {Root}/test/
  ```

  **形态 http-api / http-web**：
  ```
  {Root}/src/<module>/{__init__.py, service.py, models.py}
  {Root}/src/common/
  {Root}/agent/                     # 可选，如需 LLM 编排
  {Root}/backend/                   # FastAPI
  {Root}/doc/<module>/
  {Root}/doc/common/
  {Root}/doc/backend.md
  {Root}/doc/frontend/              # 仅 http-web
  {Root}/script/
  {Root}/test/
  ```

  **形态 mcp-server**：
  ```
  {Root}/src/<module>/{__init__.py, service.py, models.py}
  {Root}/src/common/
  {Root}/mcp-server/{__init__.py, server.py, tools/}
  {Root}/doc/<module>/
  {Root}/doc/common/
  {Root}/doc/mcp-server.md
  {Root}/script/                    # sse/http/mcpb 模式需要；stdio 不需要
  {Root}/test/
  ```

  完整目录结构示意参考 `designer.md` 的「Agent 参考架构」章节或 spec §1。
  ```

- [ ] **Step 3.3: 新增"按 Agent Type 实现"章节**

  在 `## 开发原则` 之后新增：

  ```markdown
  ## 按 Agent Type 实现

  Developer 实现时根据 feature 的 Agent Type 决定产出哪些代码：

  ### 所有形态共同
  - `src/<module>/service.py`：业务逻辑（被 CLI/Backend/MCP Server 调用）
  - `src/<module>/models.py`：dataclass + enum
  - `src/common/models.py`：跨 module 共享数据（如使用）

  ### cli-only 形态追加
  - `cli/<module>.py`：CLI wrapper（click）
  - **调用方式**：`python3 cli/<module>.py --help`（不用 `python -m`）
  - cli.py 头部需处理 sys.path：

  ```python
  import sys, os
  sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
  from src.<module>.service import <ServiceName>
  ```

  ### http-api / http-web 形态追加
  - `backend/`：FastAPI，直接 `from src.<module>.service import ...`
  - **不写 CLI**（backend 直接调 src/）
  - http-web 追加 `frontend/` 实现

  ### mcp-server 形态追加
  - `mcp-server/server.py`：MCP server 入口
  - `mcp-server/tools/`：tools 定义（每个 tool 映射到 src/ 中的方法）
  - **不写 CLI、不写 backend/**

  ### 多形态组合
  Agent Type 是单选——一个 feature 只对应一种形态。如某 agent 需要多形态（如同时 CLI + HTTP），按两个 feature 分别实现，共享 `src/`。
  ```

- [ ] **Step 3.4: 更新 `### data-schema一致性` 章节**

  找到 `### data-schema一致性`（约 line 132-148），在「新增数据字段检查清单」中追加 module 维度：

  ```markdown
  #### 新增数据字段检查清单

  新增或修改数据字段时，需同时检查以下位置：

  1. `doc/<module>/data-schema.md` — 更新 schema 定义与 dataclass（按 module 维护，不再单文件）
  2. `src/<module>/models.py` — 同步 dataclass / enum 定义
  3. **如属共享数据**：`doc/common/data-schema.md` + `src/common/models.py`
  4. CLI 序列化/反序列化（仅 cli-only 形态）
  5. 前端 JS 渲染与表单提交（仅 http-web 形态）
  6. MCP tools input/output schema（仅 mcp-server 形态）
  ```

- [ ] **Step 3.5: 更新任务输入格式中的状态字段引用**

  找到 `### 常规开发任务` 输入格式（约 line 27-46），Instructions 步骤 6「Git commit」需要兼容 migration feature：

  ```markdown
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

- [ ] **Step 3.6: 新增 `## Migration Feature 实现规范` 章节**

  在 `## Bug 修复流程` 之后新增：

  ```markdown
  ## Migration Feature 实现规范

  当 feature 标记为 `Type: migration` 时，developer 遵循以下差异：

  ### 约束
  - **纯迁移**：不改业务行为，不加新功能，不改数据格式
  - **分批迁移**：按 module 顺序迁移，一次一个 module
  - **每批验证**：每个 module 迁移后立即跑全量测试

  ### 流程
  1. 读 DESIGN.md 中的迁移方案（module 拆分边界）
  2. 创建 `src/<module>/` 目录，从旧 `cli/*.py` 抽取业务逻辑到 `service.py`
  3. 数据结构抽到 `src/<module>/models.py`
  4. 跨 module 共享部分抽到 `src/common/models.py`
  5. 创建 `cli/<module>.py` 作为 wrapper（如保留 cli-only 形态）
  6. 删除旧 `cli/*.py` 中的业务逻辑（保留 wrapper 入口）
  7. 更新 `doc/<module>/data-schema.md`（从旧 `doc/data-schema.md` 按边界拆分）
  8. 删除旧 `doc/cli.md`、`doc/data-schema.md`、`doc/data-persistence.md`
  9. 跑全量测试确认行为不变
  10. Commit（`refactor(migrate): migrate <module> to new architecture`）

  ### 不允许的操作
  - 顺手修 bug（记录到 `.issues/`，单独修复）
  - 加新字段（开新 feature）
  - 重构无关代码
  ```

- [ ] **Step 3.7: 读完整 developer.md 确认修改正确**

  Read 全文。验证：
  - 目录结构按形态分流
  - 按 Agent Type 实现章节存在
  - data-schema 一致性含 module 维度
  - Migration Feature 实现规范章节存在
  - CLI 调用方式明确为 `python3 cli/<module>.py`

- [ ] **Step 3.8: Commit**

  ```bash
  git add system-prompt/agent-factory/developer.md
  git commit -m "refactor(developer): per-Agent-Type implementation + migration feature spec"
  ```

---

### Task 4: 更新 qa.md（按 Agent Type 差异化验收）

**Files:**
- Modify: `system-prompt/agent-factory/qa.md`

按 spec §F（spec-compliance 检查项）和四种形态的验收差异落地。

- [ ] **Step 4.1: 读现有 qa.md，定位各章节**

  Read 全文。记录：
  - `## 验收工作流程`（4 个阶段）
  - `## 诊断工作流程`
  - `## QA-REPORT.md 模板`

- [ ] **Step 4.2: 新增"按 Agent Type 差异化验收"章节**

  在 `## 验收工作流程` 之前新增：

  ```markdown
  ## 按 Agent Type 差异化验收

  QA 验收时根据 feature 的 Agent Type 选择对应的验收入口：

  | Agent Type | 验收入口 | 跳过项 |
  |------------|----------|--------|
  | `cli-only` | 执行 `python3 cli/<module>.py --help` + 各子命令 | backend / frontend / mcp-server |
  | `http-api` | HTTP API 调用（启动 backend，调 REST API） | CLI / frontend / mcp-server |
  | `http-web` | Playwright 操作 Web UI（完整端到端） | CLI / mcp-server |
  | `mcp-server` | MCP client 模拟调用 tools | CLI / backend / frontend |

  ### mcp-server 形态的验收特殊性

  - 启动 mcp-server（按 Deploy Mode）
  - 用 MCP client（如 Claude Code inspector、mcp CLI）调用每个 tool
  - 验证 tool 返回结构与 `doc/mcp-server.md` 定义的 output schema 一致
  - 验证每个 tool 实际调用了 `src/<module>/service.py` 的对应方法

  ### Migration feature 的验收特殊性

  - 不验收新功能（设计上不变）
  - **重点**：迁移前后行为一致性
  - 跑全量回归测试，所有用例必须 PASS
  - 对比迁移前后的 E2E 输出（如可能）
  ```

- [ ] **Step 4.3: 更新"阶段 2：E2E 场景验收"**

  找到 `### 阶段 2：E2E 场景验收`（约 line 100-108），按 agent type 分支：

  ```markdown
  ### 阶段 2：E2E 场景验收

  按 Agent Type 选择验收入口，逐一执行每个 User Scenario：

  **cli-only**：
  1. 准备测试输入（JSON / 参数）
  2. 执行 `python3 cli/<module>.py <command> [args]`
  3. 验证输出格式与 `--help` 描述一致
  4. 验证完整链路（CLI → src/<module>/service → Data Layer）

  **http-api / http-web**：
  1. 启动 backend 服务（http-web 同时启动 frontend）
  2. 通过 HTTP API 调用（http-web 用 Playwright 操作 UI）
  3. 验证响应结构与 `doc/backend.md` 设计一致
  4. 验证完整链路（Web UI / API → Backend → src/<module>/service → Data Layer）

  **mcp-server**：
  1. 按 Deploy Mode 启动 mcp-server
  2. 用 MCP client 调用 tool
  3. 验证返回结构与 `doc/mcp-server.md` output schema 一致
  4. 验证完整链路（MCP tool → src/<module>/service → Data Layer）

  记录每个场景的执行结果和发现的问题。
  ```

- [ ] **Step 4.4: 更新"阶段 1：设计合规检查"**

  找到 `### 阶段 1：设计合规检查`（约 line 89-98），按形态调整检查项：

  ```markdown
  ### 阶段 1：设计合规检查

  对照 DESIGN.md 检查实现，按 Agent Type 启用对应检查：

  | 检查项 | cli-only | http-api | http-web | mcp-server |
  |--------|----------|----------|----------|------------|
  | 数据结构 | ✓ `doc/<module>/data-schema.md` | ✓ | ✓ | ✓ |
  | 共享数据 | ✓（如使用 common） | ✓（如使用） | ✓（如使用） | ✓（如使用） |
  | CLI 接口 | ✓ `python3 cli/<module>.py --help` 实际输出 | ✗ | ✗ | ✗ |
  | API 接口 | ✗ | ✓ `doc/backend.md` | ✓ | ✗ |
  | UI 元素 | ✗ | ✗ | ✓ `doc/frontend/` | ✗ |
  | MCP tools | ✗ | ✗ | ✗ | ✓ `doc/mcp-server.md` |
  ```

- [ ] **Step 4.5: 读完整 qa.md 确认修改正确**

  Read 全文。验证：
  - 按 Agent Type 差异化验收章节存在
  - 阶段 1 / 阶段 2 含形态分支
  - mcp-server 形态验收特殊性说明存在
  - Migration feature 验收特殊性说明存在

- [ ] **Step 4.6: Commit**

  ```bash
  git add system-prompt/agent-factory/qa.md
  git commit -m "refactor(qa): per-Agent-Type acceptance + migration feature verification"
  ```

---

### Task 5: 更新 spec-compliance.md（新检查清单 + 输入分发 + 多文件输出）

**Files:**
- Modify: `system-prompt/agent-factory/spec-compliance.md`

按 spec §4（spec-compliance 新检查清单）整体重构。

- [ ] **Step 5.1: 读现有 spec-compliance.md，了解现有结构**

  Read 全文。现有结构：
  - Review Checklist（C/S/P/B 四组）
  - Workflow
  - Output Format

- [ ] **Step 5.2: 替换"Review Checklist"章节**

  找到 `## Review Checklist`（约 line 9-53），整体替换为 spec §4.2 的检查清单：

  - 顶层说明：按 agent type 启用对应检查组
  - T 组（顶层 DESIGN.md，T1-T3）—— 沿用 spec §4.2 表格
  - S 组（data-schema，S1-S7）—— 沿用原检查项，但目标文件改为 `doc/<module>/data-schema.md`（按 module）和 `doc/common/data-schema.md`
  - P 组（data-persistence，P1-P4）—— 沿用原检查项，目标文件改为 `doc/<module>/data-persistence.md`
  - C 组（CLI，C1-C7）—— 仅 cli-only 形态，目标改为 `python3 cli/<module>.py --help` 运行时输出
  - B 组（backend，B1-B4）—— 仅 http-api/http-web，沿用原检查项
  - F 组（frontend，F1-F3）—— 仅 http-web，新增（参考 spec §4.2）
  - M 组（mcp-server，M1-M4）—— 仅 mcp-server，新增（参考 spec §4.2）

  完整内容见 spec §4.2 表格。

- [ ] **Step 5.3: 替换"Workflow"章节**

  找到 `## Workflow`（约 line 55-61），替换为：

  ```markdown
  ## Workflow

  1. 从 prompt 读取 `Agent Type`、`Modules`、`Shared Schema Changed`
  2. 启用对应检查组（参考「检查组启用矩阵」）
  3. 对每个目标文件（或运行时命令）执行检查
  4. 对 cli-only 形态，实际执行 `python3 cli/<module>.py --help` 拿输出再检查
  5. 汇总所有文件的 violations，输出结构化 JSON

  ### 检查组启用矩阵

  | 检查组 | cli-only | http-api | http-web | mcp-server |
  |--------|----------|----------|----------|------------|
  | T（顶层） | ✓ | ✓ | ✓ | ✓ |
  | S（data-schema） | ✓ | ✓ | ✓ | ✓ |
  | P（data-persistence） | ✓ | ✓ | ✓ | ✓ |
  | C（CLI） | ✓（运行时） | ✗ | ✗ | ✗ |
  | B（backend） | ✗ | ✓ | ✓ | ✗ |
  | F（frontend） | ✗ | ✗ | ✓ | ✗ |
  | M（mcp-server） | ✗ | ✗ | ✗ | ✓ |
  ```

- [ ] **Step 5.4: 替换"Output Format"章节**

  找到 `## Output Format`（约 line 62-151），整体替换为 spec §4.3 的多文件汇总格式：

  ```markdown
  ## Output Format

  返回按 agent type 分组的多文件 violations 汇总：

  ```json
  {
    "agent_type": "http-web",
    "modules": ["financial", "news"],
    "results": [
      {
        "file": "DESIGN.md",
        "summary": { "totalChecks": 3, "passed": ["T1","T2"], "failed": ["T3"] },
        "violations": [
          {
            "checkId": "T3",
            "check": "模块划分建议",
            "lineRange": null,
            "detail": "DESIGN.md 缺少「模块划分建议」章节，本 feature 涉及新增 module 必填"
          }
        ]
      },
      {
        "file": "doc/financial/data-schema.md",
        "summary": { "totalChecks": 7, "passed": ["S1","S2","S4","S5","S6","S7"], "failed": ["S3"] },
        "violations": [
          {
            "checkId": "S3",
            "check": "枚举使用",
            "lineRange": [45, 48],
            "detail": "IncomeType 字段使用字符串常量而非 Python enum"
          }
        ]
      },
      {
        "file": "doc/common/data-schema.md",
        "summary": { "totalChecks": 7, "passed": ["S1","S2","S3","S4","S5","S6","S7"], "failed": [] }
      },
      {
        "file": "doc/backend.md",
        "summary": { "totalChecks": 4, "passed": ["B1","B2","B3"], "failed": ["B4"] },
        "violations": [
          {
            "checkId": "B4",
            "check": "调用流程图",
            "lineRange": null,
            "detail": "缺少 API → src/<module>/service 的 mermaid 调用流程图"
          }
        ]
      },
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
    ]
  }
  ```

  ### Rules

  - 每个被检查的文件一个 entry
  - `summary.passed` 列出该文件通过的所有检查 ID
  - `summary.failed` 列出该文件失败的所有检查 ID
  - `violations` 数组只包含 failed 项的详细信息
  - 如某文件全部通过，`violations` 为空数组
  - cli-only 形态的 C 组检查：file 字段写 `cli/<module>.py --help`（运行时输出），lineRange 引用输出中的行号

  ### Edge case

  如果所有文件全部通过，输出：`{"agent_type": "...", "modules": [...], "results": [...], "overall": "All checks passed"}`
  ```

- [ ] **Step 5.5: 读完整 spec-compliance.md 确认修改正确**

  Read 全文。验证：
  - 检查清单含 T/S/P/C/B/F/M 七组
  - Workflow 含按 agent type 分发逻辑
  - Output Format 含多文件汇总
  - 检查组启用矩阵存在

- [ ] **Step 5.6: Commit**

  ```bash
  git add system-prompt/agent-factory/spec-compliance.md
  git commit -m "refactor(spec-compliance): per-Agent-Type checks + multi-file output + new M/F/T groups"
  ```

---

### Task 6: 整体一致性 review

**Files:**
- Read: 所有 5 个修改后的文件 + spec

- [ ] **Step 6.1: 跨文件术语一致性检查**

  Grep 验证关键术语在 5 个文件中一致：
  ```bash
  grep -l "Agent Type" system-prompt/agent-factory/*.md
  grep -l "src/<module>" system-prompt/agent-factory/*.md
  grep -l "doc/<module>" system-prompt/agent-factory/*.md
  grep -l "mcp-server" system-prompt/agent-factory/*.md
  ```

  预期：designer.md / agent-pm.md / developer.md / qa.md / spec-compliance.md 都命中。

- [ ] **Step 6.2: 验证旧术语已被替换**

  Grep 确认旧结构术语不再出现在主流程描述中（出现在 migration flow 中是 OK 的）：
  ```bash
  grep -n "doc/cli.md" system-prompt/agent-factory/*.md
  grep -n "doc/data-schema.md" system-prompt/agent-factory/*.md
  ```

  预期：只出现在 migration / 旧结构检测的描述中。

- [ ] **Step 6.3: 跨文件引用对齐**

  验证：
  - agent-pm.md 调度 designer 的 prompt 引用 `Agent Type`
  - designer.md DESIGN.md 模板与 spec §3 一致
  - developer.md 目录结构与 designer.md 一致
  - qa.md 检查项与 spec-compliance.md 检查组对齐

- [ ] **Step 6.4: Commit（如有微调）**

  如 step 6.1-6.3 发现不一致，微调后 commit：
  ```bash
  git add system-prompt/agent-factory/*.md
  git commit -m "docs: cross-file consistency fixes for new architecture"
  ```

  如无微调，跳过此步。

- [ ] **Step 6.5: 最终汇报**

  输出汇报：
  - 5 个文件已按 spec 落地
  - 旧结构术语已替换
  - 跨文件引用对齐
  - 整体 commit 历史（约 5-6 个 commit）

---

## Self-Review

**Spec coverage**：
- §1 目录结构 → Task 1.3, 3.2 ✓
- §2 REQUIREMENTS.md 新字段 → Task 2.2 ✓
- §3 DESIGN.md 新模板 → Task 1.5 ✓
- §4 spec-compliance 新检查清单 → Task 5 ✓
- §5 共享数据新增流程 → Task 1.7 ✓
- §6 强制迁移 → Task 2.4, 2.6, 3.6 ✓
- §D Agent Type 枚举 → Task 1.4, 2.2 ✓
- §E DESIGN.md 模板 → Task 1.5 ✓
- §F spec-compliance → Task 5 ✓

**Placeholder scan**：无 TBD/TODO，每个 step 引用 spec 具体章节或给出具体内容。

**Type consistency**：术语统一为 `Agent Type`、`Deploy Mode`、`src/<module>/`、`doc/<module>/`、`src/common/`、`doc/common/`、`Type: migration`。

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-06-21-agent-architecture-refactor.md`.
