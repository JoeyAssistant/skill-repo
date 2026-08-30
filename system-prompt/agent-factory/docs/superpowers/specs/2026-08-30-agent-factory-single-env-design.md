# agent-factory 环境拓扑统一设计（prod 只读访问 + 跨环境机制退役）

- 日期：2026-08-30
- 状态：待评审
- 范围：仅 agent-factory 仓库内资产（prompt / README），CLI 不动

## 1. 背景与问题

agent-factory 当前有两套实际使用方式：

| | 工作项目 | 个人项目 |
|---|---------|---------|
| 拓扑 | 永久单机：dev 仓与 prod 部署逻辑隔离 | 过渡期双机（dev / prod 分离），终局为 dev 与 prod 一体 |
| 状态目录 | gitignore（团队协作仓，不暴露个人工作流） | 上库 |
| 跨环境机制 | 不适用 | `_incoming` 中转 |

现存痛点：

1. **两套方式不统一**：prompt 内置了 `_incoming` 跨环境中转流程，与工作场景（同机、状态不上库）不匹配
2. **跨环境传递失真**：prod 侧与用户讨论出的细节（schema 字段、规格）在中转载荷中丢失，开发结果与预期不一致
3. **同机交接断点**：工作场景 prod 发现问题后，需显式指定 dev 目录提单、再单独启动实例做需求分析
4. **同机 prod 数据访问**：定位问题需要读 prod 的 log/data，缺乏规范入口与只读保证

终局判断：个人项目走向 dev 与 prod 一体后，跨环境机制整体退役；工作项目永久单机。因此**统一方向不是融合两套流程，而是收敛为"单一工作流 + 拓扑配置（unified / split）"，跨环境机制删除**。

## 2. 目标与非目标

**目标**

- agent-factory 收敛为单一工作流 + 拓扑配置；删除 `_incoming` 跨环境机制及旧格式兼容
- 新增项目级拓扑配置（`topology: unified / split`）：split 时 PM 直读 prod 的 log/data 定位问题
- prod 只读约束：第一层 prompt 约束，第二层（建议）用户级 deny 规则
- 协作仓零足迹部署方案（工作场景）

**非目标**

- data/ 备份机制（单独考虑）
- CLI 新增子命令（配置文件由 PM 读取，不进 CLI）
- 任何具体会话驱动方的集成（agent-factory 保持载体无关，不体现具体驱动方）
- 状态仓 / 跨机同步基建（随跨环境需求一起消亡）

## 3. 总体方案

```
单一工作流（所有场景）：
  用户 ↔ PM（单实例）
           ├─ 读 .claude/agents/agent-factory.yaml 的 topology（split → 激活 prod 只读访问）
           ├─ prod 问题：提 issue → 直读 prod log/data 定位 → 调度 QA/developer
           └─ 状态持久化于 .features/ .issues/（上库与否由项目自行决定）
```

## 4. 详细设计

### 4.1 配置文件 `.claude/agents/agent-factory.yaml`（项目级）

**术语与命名约定**（全文统一）：

| 概念 | 定名 |
|------|------|
| 拓扑配置 | `topology: unified / split`，中文：dev 与 prod 一体 / dev 与 prod 分离 |
| PM 行为小节 | prod 只读访问 |
| 核心行为 | 直读（读 prod log/data，不 cp 不建 snapshot） |
| 核心约束 | 只读约束（禁写禁改禁删 prod 任何文件） |
| 约束传递 | 调度传递（调度 prompt 注明只读） |
| 部署方案 | 零足迹部署（协作仓内无 agent-factory 痕迹） |

```yaml
topology: split                  # unified（默认）= dev 与 prod 一体：单目录开发运行
                                 # split = dev 与 prod 分离：同机两个部署目录
prod:                            # topology: split 时必填
  root: /abs/path/to/prod-deploy # prod 部署根目录
  # log: /abs/path/to/prod-log   # 可选覆盖，默认 <root>/log
  # data: /abs/path/to/prod-data # 可选覆盖，默认 <root>/data
```

- **位置理由**：`.claude/agents/` 已是 agent-factory 资产落点（subagents 安装于此），配置随资产同居；对 git 零影响
- **零足迹兜底**：若团队仓跟踪了 `.claude/`，用 `.git/info/exclude` 本地排除（不写 .gitignore——.gitignore 本身进仓）
- 无配置文件 / 无 topology 键 → 视为 unified（默认），零配置可用
- 配置不含任何敏感信息（仅路径），无需脱敏

### 4.2 `agent-pm.md` 修改

**新增一：模式检测扩展**（§模式检测 追加，三分支）

> 3. 读 `.claude/agents/agent-factory.yaml` 的 topology：无配置或 `unified` → dev 与 prod 一体，无特殊行为；`split` 且 prod 完整 → 激活 prod 只读访问（见 §prod 只读访问）；`split` 但 prod.root 缺失，或 `unified` 却带 prod → 配置矛盾，启动即报错提示用户修配置

**新增二：`## prod 只读访问` 小节**（置于 §模式检测 之后），内容要点：

- **触发**：`topology: split`（log/data 默认按 `<root>/log`、`<root>/data` 约定发现，可用 `prod.log` / `prod.data` 覆盖）
- **直读**：定位问题、收集证据时直接读取 prod 下的 log/data，**不 cp、不建 snapshot**（引用时带文件路径 + 行号即可）
- **只读约束**：对 prod 路径下任何文件禁止写入 / 修改 / 删除（包括加日志、改数据）。prod 是运行现场，取证只读
- **调度传递**：PM 调度 QA / developer 涉及 prod 取证时，必须在调度 prompt 中注明 prod 路径与只读约束（subagent 不读配置文件）

**删除清单**（整章删除，连带 TOC 条目）：

| 位置 | 内容 |
|------|------|
| §生产环境模式 | 整章：工作流程、分支 A/B、生产环境 PM 约束、QA 诊断调度 prompt |
| §跨环境 Issue 处理 | 整章：`_incoming` 扫描、Step 1/2（含 NOTES.md/REQUIREMENTS.md 旧格式兼容）、bug 流程、feature-request 流程、汇报、跨环境 Bug 修复流程、QA 验证调度 prompt |
| §允许 PM 自己做的事 | "跨环境 issue（来自 `_incoming/`）：确认 snapshot 已就位" 条目 |
| §调度模板 | "跨环境 Issue 验证调度 prompt 见 §跨环境 Issue 处理" 引用行 |
| §日常巡检 | 步骤 2（检查 `_incoming`）与汇报项"来自生产环境的新报告数" |
| §基于证据举例 | "只登记了 NOTES.md" 示例改为其他文件（如 README.md） |

### 4.3 `qa.md` 修改

**删除：模式三（生产环境诊断模式）整块**，连带：

- 角色约束中两条"生产环境诊断模式"条目
- 输入格式 §模式三（含 JSON 输出格式与约束块）
- 工作模式定义中的模式三条目

**修齐：模式二（诊断模式）NOTES.md 残留 → 对齐 ISSUE.yaml + CLI 机制**（既有不同步，本轮一并修）：

| 位置 | 现状 | 改为 |
|------|------|------|
| 角色约束 | "只更新 NOTES.md 的 QA Diagnosis 章节" | "只通过 CLI 更新 ISSUE.yaml 的 root_cause / fix_plan" |
| 角色约束 / 输入格式 note | `index.md` ×2（L17/L88） | `index.yaml` |
| 输入格式·诊断模式 Instructions | "Read NOTES.md" / "Write diagnosis to NOTES.md" | "Read ISSUE.yaml（`agent-factory issue show <id>`）" / 按诊断工作流程写回 |
| 诊断工作流程步骤 1-2 | "按 NOTES.md 复现"、"在 NOTES.md 标注 Log Auditability" | 改为 ISSUE.yaml / CLI 写回表述 |
| §NOTES.md 写入规范 | 整章为旧机制 | 删除章节壳，保留并上移"fix_plan 写法"小节（内容为现行 CLI 机制，正确） |

**保留不动**：模式一（验收模式）、Agent Type 差异化验收、QA-REPORT.md 模板、严重度定义、输出格式。

### 4.4 `developer.md` 修齐（既有不同步，本轮一并修）

| 位置 | 现状 | 改为 |
|------|------|------|
| 角色约束 / Instructions（L16/39/44/103/124） | `index.md` ×5 | `index.yaml`（与 agent-pm.md 及 CLI 实际文件一致） |
| 工作流程"更新状态"（L124） | "开发完成后更新为 `done`" | "`qa-reviewing`"（done 需 QA pass 后由 PM 流转；与自身 L44/L103 及状态机一致） |

**保留**：L272/298/304 的"生产环境"为运行时日志等级语境（production runtime），与跨环境机制无关。

### 4.5 `README.md` 修改

**删除**：§生产 ↔ 开发协作（含架构图与说明）。

**新增：§零足迹部署（协作项目）**，内容要点：

1. 安装：subagents 复制到 `<project>/.claude/agents/`（developer/qa/poc.md）；若团队仓跟踪 `.claude/`，将其加入 `.git/info/exclude`
2. 状态目录本地排除：`.git/info/exclude` 追加 `.features/` `.issues/`
3. 环境配置：创建 `.claude/agents/agent-factory.yaml`，`topology: split` + `prod.root`
4. 启动（示例，别名自选）：

```bash
pm() {
  local prod_root=$(yq '.prod.root' .claude/agents/agent-factory.yaml 2>/dev/null)
  claude-glm-skip-perms \
    --append-system-prompt "$(cat <agent-factory>/agent-pm.md)" \
    ${prod_root:+--add-dir $prod_root}
}
```

5. 只读硬兜底（建议）：用户级 `~/.claude/settings.json` 添加

```json
{
  "permissions": {
    "deny": ["Edit(/abs/path/to/prod/**)", "Write(/abs/path/to/prod/**)"]
  }
}
```

6. 资产通用性声明（一句）：prompt + subagents + CLI 可在任意 Claude Code 会话中使用，驱动方式不限

### 4.6 CLI

不动。配置文件由 PM（prompt）直接读取，CLI 不感知。

## 5. 只读约束分层

| 层 | 机制 | 强度 | 状态 |
|----|------|------|------|
| 1 | prompt 约束（PM 小节 + 调度传递） | 软约束（模型遵从） | 本轮落地 |
| 2 | 用户级 deny 规则（`~/.claude/settings.json`） | harness 硬拦截，对 subagent 同样生效 | 本轮写入文档建议 |
| 3 | OS 级（chmod 444 / 只读挂载） | 绝对 | 不在本轮 |

## 6. 验证清单

**E2E（实施后）**

1. fixture prod 目录 + 配置文件 → 启动 PM → 报 prod 问题 → PM 提 issue（`agent-factory issue new`）→ 直读 fixture 日志定位 → 结论引用路径+行号
2. 诱导 PM 写 prod 文件 → prompt 层拒绝
3. PM 调度 QA 诊断 → QA 调度 prompt 含 prod 只读约束
4. 工作仓 `git status` 全程无 agent-factory 痕迹（exclude 生效）
5. 全文 grep `_incoming` / `NOTES.md` / `REQUIREMENTS.md` / `生产环境` 在 agent-pm.md / qa.md / README.md 三个文件中零残留；`index.md` 在全部 prompt 文件零残留（统一为 index.yaml）

## 7. 迁移影响

- `_incoming` 机制删除后，仍按旧流程提交的跨环境报告**没有自动接收方**，过渡期手动处理（已知并接受；个人项目终局为单环境，不再需要中转）
- 旧格式（NOTES.md / REQUIREMENTS.md）兼容层随章节删除——历史目录中的旧文件如有保留价值，纯归档，不再进流程
- 上游使用方（如外部 agent 的问题反馈提示词）若引用了 `_incoming` 约定，由其各自后续自行调整，agent-factory 不做兼容承诺

## 8. 实施切分建议

1. `agent-pm.md`：删跨环境两章 + 连带引用 → 加模式检测扩展 + prod 只读访问小节
2. `qa.md`：删模式三 + 修齐模式二（含 index.md）
3. `developer.md`：修齐 index.md / done 两处
4. `README.md`：删协作章节 + 加零足迹部署
