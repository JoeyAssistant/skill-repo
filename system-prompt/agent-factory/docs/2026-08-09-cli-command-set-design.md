# CLI Command Set Design

**Date**: 2026-08-09
**Status**: Draft（待用户 review）
**Scope**: 为 agent-factory 设计 CLI 命令集，让 PM (agent) 通过 shell 操作 YAML 需求文档

---

## 1. Background

### 1.1 当前状态

agent-factory 已实现 pydantic schema（Feature / Issue / FeatureIndex / IssueIndex / BlockedRecord）+ 单一 `validate.py` CLI 入口。

### 1.2 痛点

- **PM 必须手写 YAML**：当前工作流教 PM 直接编辑 `.features/<id>/REQUIREMENTS.yaml`，agent 通过 shell 操作 YAML 字符串容易出错（escape、缩进、字段顺序）
- **独立 validate 命令冗余**：如果所有 YAML 操作都通过 CLI，CLI 写入时校验就够，不需要事后 validate
- **缺少 scaffold / set / transition 等操作命令**：PM 没有结构化接口编辑需求文档

### 1.3 目标

- **CLI 完整接管**：PM 永远通过 CLI 命令读写 YAML，不手写
- **CLI 写入时校验**：每个写操作命令内部用 pydantic schema 校验，文件永远合法
- **删除独立 validate 命令**：作为 CLI 命令集的一部分被取代
- **agent-pm.md 简化**：教 PM 用 CLI 命令，不再教直接改 YAML

---

## 2. Core Decisions

### 2.1 调用环境：只 PM (agent)，无交互式

PM 通过 Claude Code 的 shell 调用 CLI。无交互式 prompt、无 `$EDITOR` 集成、无 TUI。

**含义**：
- 所有输入通过命令行参数或 `--file <path>`
- 输出适合 agent 解析（结构化、清晰）
- 错误信息精确到字段路径

### 2.2 命令组织：`<resource> <action>`

与 docker / kubectl 风格一致。`agent-factory feature new` / `agent-factory issue show 1` / `agent-factory index refresh`。

便于未来扩展资源类型（如 `agent-factory doc ...` 操作 doc/）。

### 2.3 多行文本输入：参数 + `--file`

- 短文本字段（title / agent_type / priority 等）：直接 argument
- 长文本字段（description / problem / data_schema 等）：`--file <path>` 从文件读
- PM 在 shell 里用 heredoc 写到临时文件，然后 `--file /tmp/xxx.md`

### 2.4 目录命名：<NNN>-<slug>

- 目录：`.features/<NNN>-<slug>/`（如 `.features/057-cli-only-data-access/`）
- NNN：3 位补零 id（保持字典序 = 数字序）
- slug：kebab-case 英文（人类可读 + URL/git 友好）
- title 字段 = 目录名（如 `"057-cli-only-data-access"`）
- title 不可改（创建时确定，rename 目录 = YAGNI）

### 2.5 命令组按文件归属分离

| 命令组 | 主要操作文件 | 跨文件特例 |
|--------|------------|----------|
| `feature` | REQUIREMENTS.yaml | `new` / `delete` 联动 index；`transition` / `block` / `unblock` 联动 index.status |
| `issue` | ISSUE.yaml | 同上 |
| `index` | index.yaml | `refresh` 扫描所有内容文件 |

### 2.6 `title` 字段不可改

`title` 在创建时通过 `--slug` 确定（`<NNN>-<slug>`），写入 REQS.yaml 和 index.yaml。

- `feature/issue set <id> title ...` 不允许（title 不在可写字段集中）
- `index set feature <id> title ...` 不允许
- 修改目录名 = YAGNI，如需改名需手动操作

### 2.7 命令集范围：最小集（17 个命令）

按 KISS，只覆盖 PM 日常工作流必需操作。复杂操作（如 add-decision / add-option）通过 `feature set <id> decisions --file <yaml>` 整体替换 list 字段。

### 2.8 删除独立 validate 命令

CLI 写入时校验，文件永远合法。删除 `agent-factory-validate` console_script，保留内部 utility 函数被新 CLI 复用。

---

## 3. Command Set（17 个命令）

### 3.1 feature 命令组（8 个）

#### `feature new` -- 创建 feature（draft 状态）

```
agent-factory feature new --title <title> --slug <slug> [--agent-type <type>] [--priority <priority>]
```

**参数**：
- `--title`（必填）：一句话标题（人类可读，存入 REQUIREMENTS.yaml，但 CLI 使用 `--slug` 生成目录名和 title 字段）
- `--slug`（必填）：目录 slug（kebab-case，如 `income-module`）
- `--agent-type`（可选，默认 `cli-only`）：`cli-only` / `http-api` / `http-web` / `mcp-server`
- `--priority`（可选，默认 `P2`）：`P1` / `P2` / `P3`

**行为**：
1. 扫描 `.features/index.yaml` 取 max(id) + 1 作为新 id
2. 生成目录名 `<NNN>-<slug>`（如 `001-income-module`）
3. 创建 `.features/<NNN>-<slug>/REQUIREMENTS.yaml`（含 id / title=`<NNN>-<slug>` / agent_type；problem / benefit / description 为空字符串占位等待 set 命令填）
4. 在 `.features/index.yaml` 添加一行：`{id, title=<NNN>-<slug>, status: draft, priority}`
5. 输出：`Created feature <id>: <NNN>-<slug>`

**slug 校验**：kebab-case（小写字母开头，小写字母/数字/连字符，正则 `^[a-z][a-z0-9-]*$`）。

**Exit codes**：0 成功 / 1 校验失败 / 2 文件已存在 / 4 slug 格式错误

#### `feature set` — 更新 REQS 字段

```
agent-factory feature set <id> <field> [value | --file <path>]
```

**参数**：
- `<id>`：feature 编号
- `<field>`：字段名（见下表）
- `[value]`：字段值（短文本）
- `[--file <path>]`：从文件读字段值（长文本）

**支持字段 + 路由**：

| field | 写入目标 | 输入方式 |
|-------|---------|---------|
| `agent_type` | REQS | value |
| `problem` | REQS | value 或 --file |
| `benefit` | REQS | value 或 --file |
| `description` | REQS | value 或 --file |
| `data_schema` | REQS | --file 推荐 |
| `interfaces` | REQS | --file 推荐 |
| `acceptance_cases` | REQS | --file 推荐 |
| `decisions` | REQS | --file（整体替换 list） |

> **注意**：`title` 不在可写字段中。title 在创建时通过 `--slug` 确定为 `<NNN>-<slug>`，不可修改。

**行为**：
1. Load REQS.yaml
2. 修改指定字段（如 `--file` 则从文件读）
3. pydantic 校验整个 Feature 对象
4. 写回 REQS.yaml
5. 输出：`Updated feature <id>: <field>`

**Exit codes**：0 成功 / 1 校验失败 / 2 feature 不存在

#### `feature transition` — 状态流转（含跨字段校验）

```
agent-factory feature transition <id> --to <status>
```

**参数**：
- `<id>`：feature 编号
- `--to`：目标状态（`draft` / `designing` / `approved` / `implementing` / `qa-reviewing` / `done` / `cancelled`）

**校验规则**：

| 流转 | 跨字段校验 |
|------|----------|
| `* → draft` | 无 |
| `draft → designing` | `description` 非空 |
| `designing → approved` | `data_schema` + `interfaces` + `acceptance_cases` 都非空 |
| `approved → implementing` | 所有 `decisions[].status == closed` |
| `implementing → qa-reviewing` | 无 |
| `qa-reviewing → done` | 无 |
| `* → cancelled` | 无（终态） |
| 其他 | 拒绝（状态路径非法） |

**行为**：
1. Load index.yaml 拿当前 status
2. 校验 `current → target` 路径合法
3. Load REQS.yaml，跑跨字段校验
4. 通过：更新 index.yaml 的 status + 写 updated 时间戳
5. 失败：stderr 输出哪些字段缺/不合法，文件不动
6. 输出：`Transitioned feature <id>: <old_status> → <new_status>`

**Exit codes**：0 成功 / 1 校验失败 / 2 feature 不存在 / 3 状态路径非法

#### `feature show` — 查看 feature

```
agent-factory feature show <id> [--format markdown|yaml|json]
```

**输出格式**：
- `markdown`（默认）：渲染为可读 markdown（含标题、字段块、decisions 列表）
- `yaml`：原始 YAML
- `json`：JSON（适合 PM 程序化解析）

**Exit codes**：0 成功 / 2 feature 不存在

#### `feature list` — 列出 features

```
agent-factory feature list [--status <status>] [--priority <priority>]
```

**输出**：默认表格（id / title / status / priority），`--format json` 切换 JSON。

**Exit codes**：0 成功

#### `feature block` — 阻塞 feature

```
agent-factory feature block <id> --reason <text> --action <text>
```

**行为**：
1. 创建 `.features/<id>/BLOCKED.yaml`（含 reason / action）
2. 更新 `.features/index.yaml` 的 status=blocked
3. 输出：`Blocked feature <id>: <reason summary>`

**Exit codes**：0 成功 / 1 已 blocked / 2 feature 不存在

#### `feature unblock` — 解除阻塞

```
agent-factory feature unblock <id> --to <status>
```

**参数**：
- `<id>`：feature 编号
- `--to`：恢复到的目标状态（PM 显式指定，如 `designing` / `implementing`）

**行为**：
1. 删除 `.features/<id>/BLOCKED.yaml`
2. 更新 `.features/index.yaml` 的 status 为 `--to` 指定的值
3. 校验转换路径合法（`blocked → <target>` 必须是合法路径）
4. 输出：`Unblocked feature <id>: status → <target>`

**为什么需要 `--to`**：blocked 状态可能是从任何状态进入的（designing / implementing），不存"前状态"，PM 必须显式指定恢复目标。

**Exit codes**：0 成功 / 1 未 blocked / 2 feature 不存在 / 3 状态路径非法

#### `feature delete` — 删除 feature

```
agent-factory feature delete <id> [--force]
```

**行为**：
1. 默认要求确认（但 PM 调用不交互，所以 `--force` 必填，否则报错）
2. 删除 `.features/<id>/` 整个目录
3. 从 `.features/index.yaml` 移除对应行
4. 输出：`Deleted feature <id>`

**Exit codes**：0 成功 / 1 未传 --force / 2 feature 不存在

---

### 3.2 issue 命令组（7 个）

结构与 feature 命令组对称。

#### `issue new --title --slug --type <bug|feature-request> [--priority]`

创建 ISSUE.yaml + index 行。`--type` 和 `--slug` 必填。目录名：`<NNN>-<slug>`。

#### `issue set <id> <field> [value|--file]`

支持字段：`scenario` / `impact` / `root_cause` / `fix_suggestion` / `fix` / `resolution`。

> **注意**：`title` 不在可写字段中，创建时通过 `--slug` 确定。

#### `issue transition <id> --to <status>`

状态路径：`open → triaging → closed`。

#### `issue show <id> [--format markdown|yaml|json]`

#### `issue list [--status --type]`

#### `issue block <id> --reason --action` / `issue unblock <id>`

---

### 3.3 index 命令组（2 个）

#### `index set feature|issue <id> <field> <value>`

```
agent-factory index set feature <id> priority P1
agent-factory index set issue <id> status closed
agent-factory index set issue <id> type bug
```

**支持字段**：
- feature: `priority` / `status`（escape hatch，通常用 feature transition）
- issue: `priority` / `status` / `type`

**不允许**：`title`（创建时通过 `--slug` 确定，不可修改）

**Exit codes**：0 成功 / 1 字段不允许 / 2 entry 不存在

#### `index refresh [feature|issue]`

扫描 `.features/*/` 目录重建 `.features/index.yaml`（issue 同理）。title = 目录名。

**用途**：CI 检查、index 损坏修复、历史数据迁移。

**Exit codes**：0 成功

---

## 4. Error Handling

### 4.1 Exit Codes

| Code | 含义 | 示例 |
|------|------|------|
| 0 | 成功 | 命令完成 |
| 1 | 校验失败 | pydantic ValidationError / 跨字段约束失败 |
| 2 | 资源不存在 | feature id 找不到 / 文件不存在 |
| 3 | 状态机违规 | transition 路径非法 / 已 blocked 时再 block |
| 4 | 参数错误 | 必填参数缺失 / 字段名 typo |

### 4.2 错误输出格式

所有错误输出到 stderr，格式：

```
Error: <错误类型>
  <错误详情>
  Context: <相关字段路径或文件路径>
```

示例：

```
Error: ValidationError
  Feature.agent_type: 'unknown-type' is not a valid AgentType
  Context: .features/1/REQUIREMENTS.yaml
```

### 4.3 成功输出格式

成功输出到 stdout，简洁一行（适合 agent 解析）：

```
Created feature 5: 收入管理模块
Updated feature 1: problem
Transitioned feature 1: draft → designing
```

`show` / `list` 命令的多行输出（markdown / yaml / json）也走 stdout。

---

## 5. State Machine Validation

### 5.1 单字段校验（pydantic 模型本身）

每个 `set` 命令写入前 pydantic 校验整个对象。校验失败：exit 1，文件不动。

### 5.2 跨字段校验（transition 命令内）

`transition` 命令读 REQS + 改 index.status 时跑跨字段校验（详见 3.1.3 表）。

校验失败：exit 1，文件不动，stderr 输出缺哪些字段。

### 5.3 状态路径校验

合法转换路径表（CLI 内置）：

```
draft → designing, cancelled
designing → approved, blocked, cancelled
approved → implementing, cancelled
implementing → qa-reviewing, blocked
qa-reviewing → done, implementing  # QA fail 回 implementing
blocked → <原状态>  # 通过 unblock 命令
done → (终态)
cancelled → (终态)
```

非法路径：exit 3。

---

## 6. Implementation Notes

### 6.1 文件组织

```
agent_factory/
  __init__.py
  schema/                  # 已存在（pydantic 模型）
    __init__.py
    enums.py
    feature.py
    issue.py
    index.py
    blocked.py
    validate.py            # 改造：删除 CLI 入口，保留 utility 函数
  cli/                     # 新增
    __init__.py            # main entry（click group）
    feature.py             # feature 命令组
    issue.py               # issue 命令组
    index.py               # index 命令组
    common.py              # shared utilities (yaml load/dump, error format)
```

### 6.2 pyproject.toml 更新

```toml
[project.scripts]
agent-factory = "agent_factory.cli:main"  # 替换原 agent-factory-validate
```

### 6.3 CLI 框架

- 使用 click（pyproject.toml 已有依赖）
- 每个命令组是一个 `click.Group`
- 主入口 `agent_factory.cli:main` dispatches 到子命令组

### 6.4 与现有 schema 的关系

- 100% 复用现有 `agent_factory/schema/*.py` 的 pydantic 模型
- CLI 命令内部 load YAML → pydantic validate → 修改 → dump YAML
- `validate.py` 改造：删除 `if __name__ == "__main__"` 和 click 命令装饰器，保留 `_load_yaml` / `_format_error` 等 utility 函数被新 CLI 复用

### 6.5 测试策略

每个命令至少 3 个测试：
- happy path（成功案例）
- 校验失败（pydantic 错误）
- 资源不存在

状态机校验额外测试：每个 transition 路径合法/非法。

---

## 7. Integration with agent-pm.md

### 7.1 工作流改造

agent-pm.md 中所有"PM 编辑 YAML"的描述改为"PM 调用 CLI 命令"。

**示例 - 创建 feature**：

```
之前：
  PM 在 .features/1/REQUIREMENTS.yaml 写 yaml 内容

现在：
  $ agent-factory feature new --title "收入管理" --slug income-module --agent-type cli-only --priority P1
  $ agent-factory feature set 1 problem "$(cat /tmp/problem.md)"
  $ agent-factory feature set 1 benefit "集中记录收入流水"
  $ agent-factory feature set 1 description --file /tmp/desc.md
```

### 7.2 跨环境 _incoming 流程

生产环境 PM 创建 ISSUE.yaml 改为调用 CLI（如果生产环境也装了 agent-factory CLI）。

或者：生产环境不装 CLI，仍然手写 YAML（特殊场景允许），开发环境用 `index refresh` 修复。

### 7.3 与 doc/ 阶段的协作

PM 在 designing 阶段直接编辑 `doc/<module>/*.md`（这部分是 markdown，不走 CLI）。CLI 只管 `.features/` 和 `.issues/` 下的 YAML 文件。

---

## 8. Out of Scope

### 8.1 不实施

- **`add-decision` / `add-option` 等细粒度 list item 操作**：用 `feature set <id> decisions --file <yaml>` 整体替换
- **`archive` 命令**：feature 完成 (status=done) 后留在原处，不归档
- **`migrate` 命令**：存量 markdown 文件不批量迁移（按 YAML schema migration design 第 4.3 节）
- **多用户/权限**：CLI 假设单用户操作
- **网络/远程操作**：CLI 只操作本地文件系统
- **`config` 命令**：当前没有可配置项

### 8.2 后续可扩展

- `agent-factory doc <action>`：操作 doc/ 目录的 markdown 文件
- `agent-factory scaffold <template>`：从模板创建项目结构
- `agent-factory stats`：统计 feature/issue 数量、状态分布等

---

## 9. Tradeoffs

### 9.1 CLI 完整接管的代价

**好处**：
- 文件永远合法（写入时校验）
- PM 不需要处理 YAML escape / 缩进
- agent-pm.md 简化（不教 YAML 编辑细节）

**代价**：
- CLI 命令集必须覆盖所有 PM 操作；某操作未覆盖时 PM 卡住
- 用户不能直接 vim 改 YAML（强行改后用 `index refresh` 兜底）

### 9.2 命令组分离的代价

**好处**：
- 命令边界清晰（一个命令主要动一个文件）
- 失败回滚简单

**代价**：
- `feature new` / `feature delete` 仍然跨文件（特例）
- 状态机校验跨文件（读 REQS + 改 index）

### 9.3 `decisions` 整体替换 vs 细粒度操作

**整体替换**：
- 命令简单（只有 `feature set <id> decisions --file <yaml>`）
- PM 写小 yaml 文件
- 多 decision 一次性更新

**细粒度操作**：
- 命令多（add-decision / set-decision / add-option / remove-option）
- PM 单字段编辑方便

按 KISS 选整体替换。如果未来 PM 反馈不方便，再加细粒度命令。

---

## 10. Next Steps

1. 用户 review 本 spec
2. 反馈确认后，invoke `superpowers:writing-plans` skill 创建实施 plan
3. 实施 plan 包括：
   - 创建 `agent_factory/cli/` 目录结构
   - 实现 17 个命令（含 happy path / 错误处理 / 状态机校验）
   - 删除独立 validate CLI 入口（保留 utility 函数）
   - 更新 pyproject.toml console_scripts
   - 更新 agent-pm.md（教 PM 用 CLI）
   - 测试覆盖（每命令至少 3 个测试）
