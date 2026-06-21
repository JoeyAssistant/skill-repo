# Agent Architecture Refactor Design

**日期**: 2026-06-21
**作者**: 用户 + Claude（brainstorming 协作）
**状态**: Draft（待用户 review）

## 背景

agent-factory 当前架构（`designer.md` 中的 Agent 参考架构）在实际使用中暴露两个核心问题：

### 问题一：CLI 中心化导致形态 2 不合理

当前两种 agent 形态都通过 CLI 调用业务逻辑：

- **形态 1（纯 CLI）**：用户通过 Claude Code 或 nanobot 调用 CLI——合理
- **形态 2（HTTP 服务/前端）**：Backend 通过 CLI 调用业务逻辑——不合理

形态 2 的问题：
- 效率低（每次调用走子进程）
- 模块间调用复杂（CLI 之间互相 shell out）
- 代码体量增大后维护成本高
- Python 模块直接 import 本应是更自然的方式

### 问题二：data-schema 单文件难维护

所有数据结构集中在 `doc/data-schema.md` 单文件，体量大时阅读、维护、协作都困难。

## 目标

- **能力模块化**：Python module 作为业务逻辑唯一载体
- **形态分流**：明确 agent 类型，按类型产出不同 artifact，避免"一种结构塞所有场景"
- **高内聚低耦合**：module 内聚，跨 module 共享数据独立管理
- **Designer 职责扩展**：从纯接口设计扩展到模块划分建议 + 形态决策

## 决策汇总

| # | 决策点 | 结论 |
|---|--------|------|
| **A** | Module 物理布局 | 方案 3：`src/<module>/` 内聚代码 + `doc/<module>/` 内聚文档 |
| **B** | 共享数据归属 | X1：新建 `src/common/` + `doc/common/data-schema.md` 承载 User/AuditLog/Pagination 等共享 entity |
| **C** | 形态 2 是否要 CLI | 完全不需要，形态 2 直接 backend → src/ |
| **D** | Agent Type 枚举 | 四分法：`cli-only` / `http-api` / `http-web` / `mcp-server`；mcp-server 子模式 `stdio` / `sse` / `http` / `mcpb` 全纳入；由 PM 在 REQUIREMENTS.md 写明 |
| **E** | DESIGN.md 模板 | 新增 `Agent Type` / `模块划分建议`；数据结构与持久化下沉到 module 粒度；接入层（CLI/Backend/MCP/Frontend）按 agent type 选其一 |
| **F** | spec-compliance 检查 | 按 agent type 分发；CLI 检查从静态读 markdown 改为运行时执行 `--help`；新增 M（mcp）/F（frontend）/T（顶层）检查项 |
| **G** | 共享数据新增流程 | Designer 在 DESIGN.md「模块划分建议」提议 → PM review → 用户确认 → 写入 `doc/common/data-schema.md` |
| **H** | 存量项目过渡 | 强制迁移；PM 启动时检测旧结构主动提醒；走 migration feature 流程；不保留 legacy 提示词 |

## 详细设计

### 1. 目录结构（按 Agent Type）

四种形态的目录结构差异如下表：

| Artifact | `cli-only` | `http-api` | `http-web` | `mcp-server` |
|----------|-----------|-----------|-----------|--------------|
| `src/<module>/{service,models}.py` | ✓ | ✓ | ✓ | ✓ |
| `src/common/models.py`（共享数据） | ✓（如需） | ✓（如需） | ✓（如需） | ✓（如需） |
| `doc/<module>/{data-schema,data-persistence}.md` | ✓ | ✓ | ✓ | ✓ |
| `doc/common/data-schema.md` | ✓（如需） | ✓（如需） | ✓（如需） | ✓（如需） |
| `cli/<module>.py` | ✓ | ✗ | ✗ | ✗ |
| `agent/` | ✗ | ✓（如需 LLM 编排） | ✓（如需 LLM 编排） | ✗（mcp 直接调 src） |
| `backend/` | ✗ | ✓ | ✓ | ✗ |
| `doc/backend.md` | ✗ | ✓ | ✓ | ✗ |
| `doc/frontend/` | ✗ | ✗ | ✓ | ✗ |
| `mcp-server/` | ✗ | ✗ | ✗ | ✓ |
| `doc/mcp-server.md` | ✗ | ✗ | ✗ | ✓ |
| `script/`（部署脚本） | ✗ | ✓ | ✓ | ✓（sse/http/mcpb 模式需要；stdio 不需要） |

#### 1.1 形态 cli-only 完整结构

```
{Root}/
  src/
    financial/
      __init__.py
      service.py            # 业务逻辑
      models.py             # dataclass + enum
    news/
      ...
    common/                 # 共享数据（可选，按需创建）
      __init__.py
      models.py
  cli/
    financial.py            # python3 cli/financial.py --help
    news.py
  doc/
    financial/
      data-schema.md
      data-persistence.md
    news/
      data-schema.md
      data-persistence.md
    common/                 # 共享数据 schema（可选）
      data-schema.md
  test/
```

#### 1.2 形态 http-web 完整结构

```
{Root}/
  src/
    financial/
      __init__.py
      service.py
      models.py
    news/
      ...
    common/
      __init__.py
      models.py
  agent/                    # 可选，如需 LLM 编排
  backend/                  # FastAPI
  doc/
    financial/
      data-schema.md
      data-persistence.md
    news/
      ...
    common/
      data-schema.md
    backend.md
    frontend/
      index.html
      ...
  script/                   # start.sh / stop.sh / status.sh
  test/
```

#### 1.3 形态 mcp-server 完整结构

```
{Root}/
  src/
    financial/
      __init__.py
      service.py
      models.py
    common/
      __init__.py
      models.py
  mcp-server/               # MCP server 适配层
    __init__.py
    server.py               # MCP server 入口
    tools/                  # tools 定义
  doc/
    financial/
      data-schema.md
      data-persistence.md
    common/
      data-schema.md
    mcp-server.md           # tools 清单 + deploy mode + 调用流程
  script/                   # sse/http/mcpb 模式需要；stdio 不需要
  test/
```

#### 1.4 CLI 调用方式

所有 CLI 调用使用脚本方式：`python3 cli/<module>.py --help`（不使用 `python -m src.<module>.cli`）。

`cli/<module>.py` 内部通过绝对路径 import `src` 业务逻辑：

```python
# cli/financial.py
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.financial.service import FinancialService
# ... click 命令定义
```

### 2. REQUIREMENTS.md 调整

PM 与用户讨论需求时，新增字段：

```markdown
## Feature
- **ID**: #<NNN>
- **Name**: <kebab-case-name>
- **Priority**: P1 | P2 | P3
- **Created**: <YYYY-MM-DD>
- **Agent Type**: cli-only | http-api | http-web | mcp-server      # ← 新增
- **Deploy Mode**: stdio | sse | http | mcpb                       # ← 新增（仅 mcp-server 时填）
```

PM 在讨论 Background 时主动询问：
- 这个 agent 怎么用——给 Claude Code 当工具（cli-only），还是提供 API（http-api），还是有网页（http-web），还是 MCP 工具（mcp-server）？
- mcp-server 形态追加问：怎么部署——本地 stdio / 远程 sse / 远程 http / 打包 mcpb？

### 3. DESIGN.md 新模板

```markdown
# <Title>

## Agent Type
<!-- cli-only | http-api | http-web | mcp-server -->
<!-- mcp-server 时附加：Deploy Mode: stdio | sse | http | mcpb -->

## 概述
<!-- 背景、目标、与现有模块的关系 -->

## 模块划分建议
<!-- 仅在涉及模块边界变化时写（新增 module、调整现有边界）。纯 module 内修改跳过此章节 -->
<!-- Designer 给建议，PM review 时和用户确认，用户拍板 -->
<!-- 内容：建议的 module 列表、各 module 职责边界、依赖关系（mermaid） -->
<!-- 如有共享数据提议，在本章节子节列出 -->

### 提议 common 数据结构（如有）
<!-- 结构名、dataclass 定义、使用方（≥2 module）、理由 -->

## 各 Module 设计

### <Module-A>
#### 数据结构
<!-- 引用 doc/<module-A>/data-schema.md，列关键 entity -->
#### 持久化
<!-- 引用 doc/<module-A>/data-persistence.md -->
#### Service 接口
<!-- src/<module-A>/service.py 暴露的核心方法签名 -->

### <Module-B>
...

## 接入层设计（按 agent type 选其一，其他删除）

### CLI（仅 cli-only）
<!-- 每个 cli/<module>.py 的参数、JSON I/O 格式、错误码 -->

### Backend（http-api / http-web）
<!-- API 路由清单、请求/响应结构、调用流程（mermaid） -->

### MCP Server（mcp-server）
<!-- tools 清单（name/desc/input schema/output schema）、调用流程（mermaid） -->

## Frontend（仅 http-web）
<!-- 页面清单、关键交互 -->

## 与现有模块的关系
<!-- mermaid 图 + 依赖/被依赖说明 -->

## Doc 变更清单
<!-- 列出受影响的 doc 文件及变更类型 -->
```

### 4. spec-compliance 新检查清单

#### 4.1 输入格式

Designer 调用 spec-compliance 时，传入 Agent Type + module 列表 + 共享数据状态：

```
## Task
检查 feature #NNN spec 合规性

## Agent Type
cli-only | http-api | http-web | mcp-server

## Modules
- <module-A>
- <module-B>

## Shared Schema Changed
true | false

## Feature Directory
<Root>/.features/<NNN>-<name>/
```

#### 4.2 检查清单（按 agent type 启用）

| 检查组 | 适用形态 | 检查对象 |
|--------|----------|----------|
| **T**（顶层） | 所有 | DESIGN.md（Agent Type、模块划分） |
| **S**（data-schema） | 所有 | `doc/<module>/data-schema.md`（按 module 分别检查）+ `doc/common/data-schema.md`（如 Shared Schema Changed=true） |
| **P**（data-persistence） | 所有 | `doc/<module>/data-persistence.md`（按 module 分别检查） |
| **C**（CLI） | cli-only | `python3 cli/<module>.py --help` 运行时输出（C1-C7 沿用原 cli.md 检查项） |
| **B**（backend） | http-api / http-web | `doc/backend.md`（B1-B4 沿用原检查项） |
| **F**（frontend） | http-web | `doc/frontend/`（F1-F3 新增） |
| **M**（mcp-server） | mcp-server | `doc/mcp-server.md`（M1-M4 新增） |

**新增检查项详情**：

| # | 检查 | 通过标准 |
|---|------|----------|
| T1 | Agent Type 字段必填且合法 | 值 ∈ {cli-only, http-api, http-web, mcp-server} |
| T2 | mcp-server 时 Deploy Mode 必填 | 值 ∈ {stdio, sse, http, mcpb} |
| T3 | 模块划分建议（涉及新 module 时必填） | 列出 module + 边界 + 依赖图 |
| M1 | tools 清单完整 | 每个 tool 有 name/description/input schema/output schema |
| M2 | 部署模式明确 | Deploy Mode 字段存在且合法 |
| M3 | 调用流程图 | mermaid 展示 tool → src/<module>/service 调用链 |
| M4 | tools 与 service 映射 | 每个 tool 都能映射到 src/<module>/service.py 的方法 |
| F1 | 页面清单 | 列出所有页面 html 文件 |
| F2 | 关键交互描述 | 每个页面的关键交互流程 |
| F3 | API 对应关系 | 每个页面映射到 backend 的哪些 API |

#### 4.3 输出格式

```json
{
  "agent_type": "http-web",
  "modules": ["financial", "news"],
  "results": [
    {
      "file": "DESIGN.md",
      "summary": { "totalChecks": 3, "passed": ["T1","T2"], "failed": ["T3"] },
      "violations": [...]
    },
    {
      "file": "doc/financial/data-schema.md",
      "summary": { "totalChecks": 7, "passed": [...], "failed": ["S3"] },
      "violations": [...]
    },
    {
      "file": "doc/common/data-schema.md",
      "summary": { "totalChecks": 7, "passed": [...], "failed": [] }
    },
    {
      "file": "doc/backend.md",
      "summary": { "totalChecks": 4, "passed": [...], "failed": ["B4"] }
    },
    {
      "file": "doc/frontend/",
      "summary": { "totalChecks": 3, "passed": [...], "failed": ["F2"] }
    }
  ]
}
```

### 5. 共享数据新增流程

```
Designer 发现需要 X 数据结构，且 ≥2 module 会用到
  ↓
Step 1: 在 DESIGN.md「模块划分建议」章节新增子节「提议 common 数据结构」
  - 结构名（如 AuditLog）
  - dataclass 字段定义
  - 使用方（哪些 module 会用，必须 ≥2）
  - 理由（为什么不归属单一 module）
  ↓
Step 2: PM 初步 review
  - 合理性 + 是否真共享（≥2 module）
  - 不合理 → designer 重新设计
  - 合理 → 进入用户确认
  ↓
Step 3: 用户在 DESIGN.md review 时一并确认
  - 同意 → designer 写入 doc/common/data-schema.md
  - 不同意 → designer 改为在 module 内自定义（接受冗余）或重新设计
  ↓
Step 4: Designer 写入 doc/common/data-schema.md
  - 新增 entity 章节（dataclass + 描述）
  - 各 module 在 data-schema.md 中 import 引用（不重复定义字段）
  ↓
Step 5: 继续 feature 设计
```

**边界情况**：
- 修改现有 common 结构字段：同样走 Step 1-4，并在 DESIGN.md 列出"影响的所有 module"
- Designer 误判（实际只 1 个 module 用）：PM review 阶段驳回
- 用户驳回 common 提议：designer 二选一——module 内自定义 / 重新设计避开需求
- 跨 feature 复用：Designer 设计前必须查 `doc/common/data-schema.md` 是否已有

### 6. 存量项目迁移（强制）

#### 6.1 旧结构检测规则

PM 启动巡检时扫描项目，满足任一即判定为旧结构：

```
1. 存在 doc/cli.md（单文件）
2. 存在 doc/data-schema.md（单文件，未拆分到 doc/<module>/）
```

#### 6.2 检测到旧结构时的行为

| 用户动作 | PM 行为 |
|----------|---------|
| 启动 PM（日常巡检） | 标注"⚠️ 项目结构过时"，在状态总览顶部高亮提示 |
| 查看现有 feature / issue | 允许（不阻塞读取） |
| 提交新 issue | 允许接收，但提示"建议先发起迁移 feature" |
| 新建 feature | 强制建议先迁移；用户坚持新建 → 允许，但 Designer 执行时若遇结构冲突 → blocked |
| 发起迁移 feature | 走下方迁移流程 |

**核心原则**：PM 不硬阻塞用户操作，但通过持续提醒 + subagent 自动 blocked 让迁移成为"必须做的事"。

#### 6.3 Migration Feature 流程

```
用户: "把这个项目迁移到新结构"
  ↓
PM 创建 migration feature
  - REQUIREMENTS.md 讨论时必填两项：
    - Agent Type: 用户决定迁完后的形态
    - 迁移范围: 全量 / 部分 module（建议全量）
  - 明确约束：纯迁移，不改行为，不加功能
  - .features/index.md 标记 Type: migration
  ↓
Designer 设计迁移方案
  - 扫描现有 cli/*.py，推断 module 边界
  - 设计 src/<module>/ 拆分方案（哪些函数归哪个 module）
  - 设计 doc/<module>/data-schema.md 拆分（从单文件按边界拆）
  - 列出 doc/common/data-schema.md 候选（跨 module 共享部分）
  - 用户确认方案
  ↓
Developer 分批执行（按 module）
  - 每个 module 迁移后跑全量测试，确认行为不变
  - 全部完成后删除旧文件（doc/cli.md、doc/data-schema.md 等）
  - git commit（一个迁移 feature = 一个 commit）
  ↓
QA 验收
  - 全量 E2E，确认功能与迁移前一致
  - 通过 → status=done
  - PM 下次巡检自动取消"项目结构过时"警告
```

**失败兜底**：blocked → Designer 重新设计（拆得更细）→ 重试。反复失败（>3 轮）→ 升级用户决策。

## 影响范围

### 需要修改的 prompt 文件

| 文件 | 修改内容 |
|------|----------|
| `agent-pm.md` | REQUIREMENTS.md 模板新增 Agent Type / Deploy Mode 字段；新增旧结构检测逻辑；新增 migration feature 支持；多项目巡检增加结构警告 |
| `designer.md` | Agent 参考架构图更新（src/ 中心化）；DESIGN.md 新模板；新增"模块划分建议"职责；按 agent type 选 artifact；新增共享数据提议职责 |
| `developer.md` | 新目录结构；按 agent type 实现；mcp-server 实现规范；CLI 调用方式（`python3 cli/<module>.py`） |
| `qa.md` | 按 agent type 差异化验收（CLI/Backend/MCP/Frontend 分别验收） |
| `spec-compliance.md` | 新检查清单（T/S/P/C/B/M/F）；输入格式调整（agent type 分发）；输出格式调整（多文件汇总） |
| `agent架构.drawio` | 已由用户更新，反映新架构 |

### 不需要修改

| 文件 | 原因 |
|------|------|
| `poc.md` | 技术可行性分析跟 agent 形态无关 |
| `README.md` | 安装/使用说明跟新结构兼容，可后续单独更新 |

## 开放问题（YAGNI）

- **chat-platform 形态**（Slack / Discord / 飞书 bot）：暂不纳入 Agent Type 枚举，未来按需扩展
- **手动迁移兜底**：migration feature 反复失败（>3 轮）后的"手动迁移"细节未定，先依赖升级用户决策

## 后续

转入 `writing-plans` skill，制定详细实施计划，分阶段落地以上修改。
