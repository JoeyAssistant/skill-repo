# Design Reference

> PM 设计阶段按需读取的参考手册。包含 doc/ 文件章节契约、字段设计原则、跨文件归属表等规则。
> 进入 `designing` 状态时，PM 应读本文件后再撰写 doc/。

## 目录

- [设计工作原则](#设计工作原则)
- [模块定义](#模块定义)
- [Agent参考架构](#agent参考架构)
- [doc/<module_name>/ 章节契约](#docmodule_name-章节契约)
  - [schema.md（业务数据结构定义）](#schemamd业务数据结构定义)
    - [字段设计原则（核心）](#字段设计原则核心)
    - [字段类型选型原则](#字段类型选型原则)
    - [关键原则](#关键原则)
  - [persistence.md（数据存储方案）](#persistencemd数据存储方案)
  - [service.md（Service 接口契约 + 流程 + 模块关系）](#servicemd-service-接口契约--流程--模块关系)
  - [cli.md（CLI 契约，仅暴露 CLI 的模块）](#climd-cli-契约仅暴露-cli-的模块)
  - [README.md（模块门面）](#readmemd模块门面)
- [跨文件内容归属表](#跨文件内容归属表)
- [doc/ 内容规则（最终正式文档，全 doc/ 适用）](#doc-内容规则最终正式文档全-doc-适用)
  - [适用范围](#适用范围)
  - [✅ 允许的内容](#-允许的内容)
  - [❌ 禁止的内容（过程性）](#-禁止的内容过程性)
  - [撰写自检（写完每个 doc 文件后）](#撰写自检写完每个-doc-文件后)
  - [反例（过程性内容混入 doc/，禁止）](#反例过程性内容混入-doc禁止)
- [设计文档输出规范](#设计文档输出规范)
- [CLI Layer](#cli-layer)
  - [CLI 设计原则](#cli-设计原则)
  - [CLI 设计归属（无 DESIGN.md，分三阶段）](#cli-设计归属无-designmd分三阶段)
- [Agent Layer](#agent-layer)
- [Backend Layer](#backend-layer)
- [代码目录结构](#代码目录结构)
  - [目录结构](#目录结构)
  - [CLI 调用方式](#cli-调用方式)

## 设计工作原则

- **图表优先**：流程、交互、依赖关系优先用 mermaid 表达（flowchart / sequence / state）。能用图说明的不写文字；文字仅作图的补充说明
- **聚焦核心**：文档核心是四类内容 —— 数据结构定义、CLI 定义、模块边界与依赖、接口交互。其余（背景、概述、理由）保持精简
- **可审计性**：每个设计决策都必须记录选择理由，使设计过程可追溯
- **可讨论性**：设计方案应先与用户讨论确认后再定稿，不擅自做重大架构决定

## 模块定义

**模块是 agent 系统的功能单元，提供一个独立的功能或服务。** 一个模块由以下要件构成，缺一不可：

| # | 要件 | 路径 |
|---|------|------|
| 1 | 独立源码 | `src/modules/<module_name>/` |
| 2 | 独立 CLI（仅暴露 CLI 的模块才有） | `src/modules/<module_name>/cli.py`（单文件） |
| 3 | 独立文档 | `doc/<module_name>/` |
| 4 | 独立单元测试 | `test/unit/<module_name>/` |

`doc/<module_name>/` 下的文件：

| 文件 | 内容 |
|------|------|
| `schema.md` | 业务数据结构定义 |
| `persistence.md` | 数据存储方案 |
| `service.md` | Service 接口契约 + 关键流程 + 模块关系 |
| `cli.md` | CLI 契约（仅暴露 CLI 的模块才有） |
| `README.md` | 模块门面：模块名词概念 + 模块职责 + 本模块 doc 索引 |

**命名**：`<module_name>` 统一使用下划线（`module_name`），四处路径同名。

**判别**：`src/` 下 `modules/` 之内的是模块；`src/` 下其余目录（`backend` / `frontend` / `skill` / `mcp`）不是模块。

## Agent参考架构

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
```

## doc/<module_name>/ 章节契约

每个 doc/<module_name>/ 文件按以下章节组织。撰写前对照契约，撰写后自检章节是否合规。

### schema.md（业务数据结构定义）

> 仅定义业务实体（dataclass / enum），含字段语义、值约束。**完全不涉存储**。

**应有章节**：
- 文件标题 + 一句话业务说明
- N × `## <EntityName> -- <一句话业务角色>` dataclass 定义（class 与每个 field 配文字描述）

**不应有章节**：SQLite Schema / Field Mapping / 去重 key / 不存储说明 / 变更记录

模板：

```markdown
# <Module> Schema

> 该 module 业务数据结构定义。仅定义"是什么"，不涉"怎么存"（存储见 persistence.md）。

## <EntityName> -- <一句话业务角色>

@dataclass
class <EntityName>:
    """<业务说明>"""
    field_a: str
        # <字段描述>。示例: <值>
        # 约束: <非显然约束>
```

#### 字段设计原则（核心）

Agent 设计围绕结构化数据 —— 所有业务、交互、功能都用 `dataclass` 表示和承载。`schema.md` 是单一真值。

**每个字段必须有清晰注释**，按"必需 + 按需"原则写：

1. **字段描述（必需）**：字段是什么、做什么、关键语义。不写"用途："标签 —— 描述本身就是用途
   - 复杂或易混淆字段附**示例值**（如 `# 券商名称。示例："国金证券（佣金宝）"`）
   - 字段名已经一目了然时可极简（如 `note: str = ""  # 备注（可选）`）
2. **使用场景（按需）**：仅当字段被多个 CLI/API/UI 场景使用且需要厘清时写。简单字段（仅展示 + 持久化）可省
3. **约束（按需，关键）**：仅写**非显然约束**：
   - ✅ 写："> 0"、"必须 ∈ enum"、"YYYY-MM-DD 格式"、"自动计算 = price * quantity"、"不可变"
   - ❌ 不写："非空字符串"、"必填"、"str 类型" 等显然约束（浪费空间）
   - 不强制每字段都有约束；没特殊约束就不写

**示例 1** — 详细风格（关键业务实体）：

```python
@dataclass
class <EntityName>:
    """<一句话业务角色说明>。<可选：列出主要使用场景>"""
    amount: float
        # <字段描述>。示例：5000.00
        # 约束：> 0；2 位小数
    category: <EnumName>
        # <字段描述>（值1 / 值2 / 值3）
    created_at: date
        # <字段描述>
        # 约束：自动写入当下日期；不可变
    note: str = ""
        # 备注（可选）
```

**示例 2** — 极简风格（简单数据类）：

```python
@dataclass
class <EntityName>:
    """<一句话业务角色说明>。"""
    date: str           # <字段描述>。约束：YYYY-MM-DD
    type: <EnumName>    # <字段描述>（值1 / 值2）
    price: float        # <字段描述>。约束：> 0
    quantity: int       # <字段描述>。约束：> 0，整数
    amount: float       # <字段描述> = price * quantity（service 层自动计算）
    note: str = ""      # 备注（可选）
```

**判断标准（写入字段前自查）**：

| 字段特点 | 处理 |
|---------|------|
| 描述清晰（一句话能说清做什么）+ 非显然约束有标注 | 保留 |
| 描述不清（"将来可能用到"/"看起来应该有"）| 删除（YAGNI） |

**格式一致性（强制）**：同一 schema.md 文件内所有 dataclass 必须用同一种注释格式（要么全部三维度行注释，要么全部行尾单行注释）。混用 → 违反规范。

**dos**

- 字段值存在有限集合时，优先使用枚举（Python `enum`）而非字符串常量或整数魔法值
- 数据结构命名清晰、合理，保证一致性
- 文档仅承载数据结构定义，不体现业务使用代码或持久化等其他内容

#### 字段类型选型原则

设计每个字段时，按以下原则选类型。**违反任一 = 设计缺陷**，需重新设计。

| 原则 | 反例 | 正解 |
|------|------|------|
| **str 仅用于自由文本**——需被解析/比较/计算/含结构化语义时禁用 | `value: str  # "X 个" / "无限制"` | `value_type: Enum (LIMITED / UNLIMITED)`<br>`value_count: Optional[int]` |
| **数值与单位分离**——单位写进字段名 | `timeout: str  # "30s" / "5m"` | `timeout_seconds: int` |
| **Optional 表"未提供"**——与零值区分（None ≠ 0 ≠ ""） | `count: int = 0  # 无数据时填 0` | `count: Optional[int] = None  # None = 未提供, 0 = 显式零` |
| **成组字段封装 dataclass**——N 字段一起出现一起消失 | `tag_k1: str`<br>`tag_k2: str`<br>`tag_k3: str` | `tags: list[TagItem]`（`TagItem` 含 key + value，可扩展） |

**字段自检**（写完每个字段前对照）：

| 字段类型 / 形态 | 自检 |
|---------------|------|
| `str` | 值是自由文本吗？需解析/比较/计算 → 改类型 |
| 数值字段 | 单位在字段名里吗？ |
| `Optional[X]` | None 语义是"未提供"还是"零值"？后者用默认值 |
| 多个相关字段 | 总是一起出现？若是 → 封装 dataclass |

#### 关键原则

- **每个 module 的 `schema.md` 作为该 module 数据结构的唯一真值，必须保证跨文档一致性**
- 任何 schema.md 修改需先与用户讨论

### persistence.md（数据存储方案）

> 聚焦"怎么存"——介质、Schema、读写、生命周期。**引用 schema.md 的 dataclass，不重复定义字段语义**。

**应有章节**：
- `## 存储介质`
- `## Schema`（含 CREATE TABLE / 索引 / 字段映射）
- `## 读写机制`
- `## 数据生命周期`（初始化 / 清理 / 备份）
- `## 配置`（环境变量、路径参数）

**不应有章节**：dataclass 重复定义 / 决策对比 / 实测数据 / CLI 内容

**存储介质选型**：优先 json、yaml 等简单持久化；较复杂场景使用数据库。

### service.md（Service 接口契约 + 流程 + 模块关系）

> Service.py 的实现契约。仅描述"是什么/怎么调用/怎么走流程"，**不解释"为什么这么设计"**。

**应有章节**：
- `## Service 接口`（class + 方法签名 + docstring）
- `## 关键流程`（mermaid sequence，按 use case 组织）
- `## 模块关系`（mermaid graph + 依赖说明）

**不应有章节**：方案概览 / 问题背景 / 关键技术决策 / 决策 N / 异常场景（issue 引用）/ 实测数据

### cli.md（CLI 契约，仅暴露 CLI 的模块才有）

> 设计期产出，作为 developer 实现 `src/modules/<module_name>/cli.py` 的契约。`--help` 运行时输出应与本文档一致。

**应有章节**：
- 文件标题 + 一句话说明
- N × `## <command>` 章节，每个含：
  - 功能说明（脚本用途、内部实现原理）
  - 输入 schema（arguments / options / `--json-input` 示例）
  - 输出 schema（成功响应 + 失败响应 + 错误码）
  - 使用示例（典型调用）

**不应有章节**：dataclass 定义 / 决策讨论 / 设计过程

### README.md（模块门面）

> 模块入口：讲清这个模块是什么、负责什么，并索引本模块其余 doc。**不重复** `schema.md` / `service.md` 的正文内容。

**应有章节**：
- 模块标题 + 一句话模块职责
- `## 名词概念`（本模块特有术语：名称 + 一句话定义）
- `## 模块职责`（本模块负责什么、不负责什么）
- `## 文档索引`（本模块其余 doc 文件 + 一句话说明）

**不应有章节**：数据结构定义 / 接口契约 / 决策讨论 / 变更记录

## 跨文件内容归属表

每写一段内容前，先对照下表判断归属。命中"应写到 FEATURE.yaml / 删"的，**不要写到 doc/**。

| 内容类别 | 应写到 | 不应写到 |
|---------|--------|---------|
| 业务字段定义（dataclass） | schema.md | persistence.md |
| 字段语义/约束 | schema.md（字段注释） | persistence.md |
| 内存对象（不持久化）dataclass | schema.md | persistence.md |
| CREATE TABLE / DDL | persistence.md | schema.md |
| 索引定义 | persistence.md | schema.md |
| Column ↔ 字段映射（仅非一一对应时） | persistence.md | schema.md |
| 存储介质选型理由 | persistence.md（一句话）+ FEATURE.yaml 需求规格 > 技术决策（深度） | service.md |
| 读写机制 | persistence.md | schema.md |
| 数据生命周期 | persistence.md | service.md |
| 配置（环境变量/路径） | persistence.md | service.md |
| Service 方法签名 | service.md | - |
| Service 关键流程 | service.md | - |
| 模块依赖关系 | service.md | - |
| CLI 命令清单（产品级） | FEATURE.yaml 关键接口 | cli.md |
| CLI 详细 JSON I/O schema | cli.md（仅暴露 CLI 的模块） | schema.md / service.md |
| CLI 错误码定义 | cli.md（仅暴露 CLI 的模块） | schema.md |
| CLI 使用示例 | cli.md（仅暴露 CLI 的模块） | schema.md |
| 设计决策 | FEATURE.yaml 需求规格 | doc/ |
| 决策对比（方案 A/B/C） | FEATURE.yaml 需求规格 | doc/ |
| 实测数据 / POC 命中率 | FEATURE.yaml 需求规格 | doc/ |
| Issue 引用（QA-XXX） | FEATURE.yaml 需求规格 | doc/ |
| 异常场景（接口契约） | service.md（方法 docstring） | - |
| 异常场景（issue 上下文） | FEATURE.yaml 需求规格 | service.md |
| 变更记录 / "X 已删除" | 删（不应存在任何 doc/） | 任何 |

## doc/ 内容规则（最终正式文档，全 doc/ 适用）

`{Root}/doc/` 下的所有文件是**最终正式文档**，仅承载"是什么"（定义、契约、方案），**不承载"为什么"**（决策、讨论、分析过程）。所有过程性内容只能写在 FEATURE.yaml 需求规格。

### 适用范围

所有 `{Root}/doc/` 下的 .md 文件：
- `doc/<module_name>/schema.md`、`doc/<module_name>/persistence.md`、`doc/<module_name>/service.md`、`doc/<module_name>/README.md`、`doc/<module_name>/cli.md`（仅暴露 CLI 的模块）

### ✅ 允许的内容

按文件类型分布（详见上方"doc/<module_name>/ 章节契约"和"跨文件内容归属表"）：

- `schema.md`：dataclass 定义 + 字段注释（字段关系、不变量、合法值集合写在字段注释里）
- `persistence.md`：存储方案（介质、Schema、读写机制、生命周期、配置）
- `service.md`：Service 接口 + 关键流程（mermaid sequence）+ 模块关系（mermaid graph）
- `README.md`：模块名词概念 + 模块职责 + 文档索引

### ❌ 禁止的内容（过程性）

详见上方"跨文件内容归属表"。重点：

- "本期 Constraints 明确排除..."、"留给后续 feature"、"YAGNI 排除" → 移到 FEATURE.yaml 需求规格 > 约束/原则
- 与其他 module 的对比说明（除非字段语义必需）
- 决策讨论、issue 引用、实测数据、变更记录等 → 见归属表对应行

### 撰写自检（写完每个 doc 文件后）

扫描文件内容，命中以下任一关键词即删或迁出：

| 启发式关键词 | 处理 |
|-------------|------|
| "Q1: ... A:"、问答式过程内容 | 移到 FEATURE.yaml 需求规格 |
| "决策"、"为什么"、"权衡"、"vs"、"相比" | 移到 FEATURE.yaml 需求规格 |
| "本期 Constraints 明确排除"、"YAGNI"、"留给后续"、"待定" | 移到 FEATURE.yaml 需求规格 > 约束/原则 |
| "第一版 / 第二版"、"变更记录"、"架构调整" | 删除（git history 已记录） |
| "用户补充"、"用户决策"、"讨论中确认" | 删除（已落在 FEATURE.yaml 需求规格） |

### 反例（过程性内容混入 doc/，禁止）

```markdown
### <EntityName>

@dataclass
class <EntityName>:
    ...

**设计决策**：<某设计选择的理由>。
理由：① ... ② ... ③ ...
```

正解（仅留 dataclass + 字段注释，描述清晰 + 关键约束）：

```markdown
### <EntityName> -- <一句话业务角色>

@dataclass
class <EntityName>:
    field_a: str
        # <字段描述>。约束：YYYY-MM-DD
    field_b: int
        # <字段描述>。约束：> 0
    field_c: <EnumName>
        # <字段描述>（值1 / 值2 / 值3）
```

决策"为什么共用 list" → FEATURE.yaml 需求规格。

## 设计文档输出规范

设计完成后，按以下结构输出文档到 `{Root}/doc/` 目录（无 DESIGN.md）：

| 文件 | 内容 | 条件 |
|------|------|------|
| `{Root}/doc/<module_name>/schema.md` | 该 module 业务数据结构定义（dataclass + 字段注释） | 所有模块 |
| `{Root}/doc/<module_name>/persistence.md` | 该 module 数据持久化方案 | 所有模块 |
| `{Root}/doc/<module_name>/service.md` | Service 方法签名 + 关键流程 mermaid + 跨 module 关系图 | 所有模块 |
| `{Root}/doc/<module_name>/README.md` | 模块门面：名词概念 + 模块职责 + 文档索引 | 所有模块 |
| `{Root}/doc/<module_name>/cli.md` | CLI 契约（每命令的 JSON I/O schema、错误码、使用示例） | 仅暴露 CLI 的模块 |
| `python3 {Root}/src/modules/<module_name>/cli.py --help` | CLI 命令运行时输出（无静态文件；命令清单在 FEATURE.yaml 关键接口定） | 仅暴露 CLI 的模块 |


## CLI Layer

### CLI 设计原则
- **`--help as doc`**：CLI 命令文档通过 `python3 {Root}/src/modules/<module_name>/cli.py --help` 运行时输出获得（运行期产出），包含：
    - **功能说明**：脚本用途、内部实现原理
    - **输入说明**：参数、选项、结构化输入格式
    - **输出说明**：成功/失败响应结构、错误码定义
    - **使用示例**：典型调用场景
- **设计期契约在 `doc/<module_name>/cli.md`**：暴露 CLI 的模块，设计期写 `cli.md`，含每个命令的 JSON I/O schema、错误码、使用示例，作为 developer 实现 `cli.py` 的契约。developer 实现完成后，`cli.md` 与 `--help` 输出应一致（QA 验收时机械比对）
- data-oriented：CLI 以数据为中心，提供 `data layer` 数据相关的操作，如查询、修改、新增、删除等，command 与入参设计保持精简，避免过度设计
- 结构化输入输出：除了常规 CLI 的 arguments/options，提供 json 格式输入全量入参，输出格式统一使用 json，方便代码或 agent 解析
- 使用 `click` 框架
- 使用 `dataclass` 定义 data schema
- 默认使用 `python3`

### CLI 设计归属（无 DESIGN.md，分三阶段）

暴露 CLI 的模块，CLI 设计分布在三处：

| 阶段 | 文件 | 内容 |
|------|------|------|
| `draft`（PM 与用户讨论） | FEATURE.yaml 关键接口 | 命令清单表 `\| 命令 \| 用途 \| 关键参数 \|`（产品级决策，要做哪些命令） |
| `designing`（设计） | `doc/<module_name>/cli.md` | 每命令的详细 JSON I/O schema、错误码、使用示例（设计期契约） |
| `implementing`（developer 实现） | `src/modules/<module_name>/cli.py` docstring + click decorators → 运行时 `--help` | 实现 `cli.py`，运行 `--help` 输出应与 `cli.md` 一致 |

PM 在 draft 阶段把 CLI 命令清单写到 FEATURE.yaml 关键接口；designing 阶段写 `cli.md` 详细契约；developer 实现 `cli.py` 时按 `cli.md` 写 click decorators + docstring，`--help` 输出应与 `cli.md` 一致。

## Agent Layer

- 使用 Claude SDK (Anthropic SDK) 或 Claude Agent SDK 构建 Agent
- **Agent 职责边界**：Agent 负责理解用户意图、编排任务流程、调用工具（执行实际业务逻辑的工具）
- **Agent 调用模块能力的两条路径**：
  - 经 CLI：执行 `python3 src/modules/<module_name>/cli.py <command>`（跨进程；模块未暴露 CLI 时不可用）
  - 直接 import：`from src.modules.<module_name>.service import ...`（同进程）
- Agent 通过 `src/modules/<module_name>/service.py` 完成数据操作
- 定义目标 Agent 的 system prompt，可通过 Claude Code 的 append-system-prompt 使用，也可通过 Anthropic SDK 或 Claude Agent SDK 使用，根据实际需求决定
- 实现时可参考 `/claude-api` skill

## Backend Layer

- backend 技术选型
- REST API 设计，针对每一个 API，列出接口定义，包括接口功能、输入、输出，使用 mermaid 语法列出 API 的调用流程，与内部模块（如 agent、`src/modules/<module_name>/`、data layer）的交互流程
- **Backend 直接 import `src/modules/<module_name>/service.py`，不经过 CLI**

## 代码目录结构

### 目录结构

```
{Root}/
  src/
    modules/
      <module_name>/
        __init__.py
        service.py          # 业务逻辑
        models.py           # dataclass + enum
        cli.py              # 仅暴露 CLI 的模块才有：python3 src/modules/<module_name>/cli.py --help
    backend/                # 非模块
    frontend/               # 非模块
    skill/                  # 非模块
    mcp/                    # 非模块
  doc/
    <module_name>/
      schema.md
      persistence.md
      service.md
      README.md
      cli.md                # 仅暴露 CLI 的模块才有
  test/
    unit/
      <module_name>/
```

### CLI 调用方式

所有 CLI 调用使用脚本方式：`python3 src/modules/<module_name>/cli.py --help`。

`cli.py` 内部通过绝对路径 import `src` 业务逻辑：

```python
# src/modules/<module_name>/cli.py
from pathlib import Path
import sys

# parents[3] = {Root}。深度由「模块定义」固定的 CLI 路径决定；CLI 路径变更需同步改此处
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from src.modules.<module_name>.service import <Module>Service
# ... click 命令定义
```
