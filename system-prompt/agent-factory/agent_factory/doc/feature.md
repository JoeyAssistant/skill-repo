# feature

FEATURE.yaml 的 schema / state / workflow 见 PM system prompt（部署于 `.claude/agents/agent-pm.md`）——它是这三项的**唯一真源**。
本文件不重复维护它们：重复会导致提示词与 CLI 文档漂移，而漂移没人发现。

CLI 侧约定：

- 状态文件：`.features/<NNN>-<slug>/FEATURE.yaml`（单条）+ `.features/index.yaml`（索引行）
- 子命令与参数见 `agent-factory feature <cmd> --help`

## 退出码

0 成功 / 1 校验失败 / 2 资源不存在 / 3 状态机违规 / 4 参数错误
