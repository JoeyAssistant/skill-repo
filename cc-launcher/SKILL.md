---
name: cc-launcher
description: Use when users want to manage Claude Code provider profiles - create, list, edit, delete profiles for different model providers (GLM, MiniMax, etc.), or regenerate shell startup functions
---

# cc-launcher

管理 Claude Code 多供应商配置（profile）的技能。支持创建、列出、编辑、删除 profile，以及生成 shell 启动函数。

## 触发条件

用户提到以下关键词时使用本技能：
- 创建/配置/添加 新的 provider/供应商/profile
- 列出/查看 所有 profile/供应商配置
- 编辑/修改 某个 profile
- 删除/移除 某个 profile
- 重新生成 shell 函数/启动命令
- 切换模型/供应商

## 配置文件位置

- 技能目录：`~/.claude/skills/cc-launcher/`
  - `registry.json` — 常用插件/MCP 注册表
  - `providers.json` — 已知供应商元数据
- Profile 目录：`~/.cc-launcher/profiles/<name>/`
  - `settings.json` — env + 插件 + 权限
  - `system-prompt.md` — 系统提示词（可选）
  - `mcp.json` — MCP 配置（可选）

## 操作流程

### 1. 创建 Profile

1. 读取 `providers.json`，展示已知供应商列表
2. 用户选择供应商（或输入自定义名称）
3. 如果是已知供应商且有 `doc_url`，使用 web fetch 抓取文档，提取默认配置（base_url、模型名等）
4. 交互式收集：
   - API Key（ANTHROPIC_AUTH_TOKEN）
   - 确认/修改 base_url、模型映射
   - 从 `registry.json` 选择插件（预选 universal + 匹配 providers 的条目）
   - 系统提示词（可选）
   - MCP 配置（可选）
5. 生成 profile 文件到 `~/.cc-launcher/profiles/<name>/`
6. 调用"重新生成 shell 函数"流程

### 2. 列出 Profile

1. 读取 `~/.cc-launcher/profiles/*/settings.json`
2. 展示汇总表格：名称、供应商、Base URL、默认模型、插件数量

### 3. 编辑 Profile

1. 选择要编辑的 profile
2. 显示当前配置
3. 选择修改项（env、插件、系统提示词、MCP）
4. 更新文件
5. 提示重新生成 shell 函数

### 4. 重新生成 Shell 函数

1. 扫描所有 `~/.cc-launcher/profiles/*/settings.json`
2. 为每个 profile 生成两个 shell function：
   - `claude-<name>()` — 正常模式
   - `claude-<name>-skip-perms()` — 跳过权限模式
3. 函数使用 `--settings`、`--append-system-prompt-file`、`--mcp-config` 参数
4. 替换 `~/.bashrc` 中 `# >>> Claude Code profiles - start >>>` 和 `# <<< Claude Code profiles - end <<<` 之间的内容
5. 如果标记不存在，追加到文件末尾

Shell 函数模板：

```bash
claude-<name>() {
  local _args="--settings $HOME/.cc-launcher/profiles/<name>/settings.json"
  test -f "$HOME/.cc-launcher/profiles/<name>/system-prompt.md" && _args="$_args --append-system-prompt-file $HOME/.cc-launcher/profiles/<name>/system-prompt.md"
  test -f "$HOME/.cc-launcher/profiles/<name>/mcp.json" && _args="$_args --mcp-config $HOME/.cc-launcher/profiles/<name>/mcp.json"
  claude $_args
}

claude-<name>-skip-perms() {
  local _args="--settings $HOME/.cc-launcher/profiles/<name>/settings.json"
  test -f "$HOME/.cc-launcher/profiles/<name>/system-prompt.md" && _args="$_args --append-system-prompt-file $HOME/.cc-launcher/profiles/<name>/system-prompt.md"
  test -f "$HOME/.cc-launcher/profiles/<name>/mcp.json" && _args="$_args --mcp-config $HOME/.cc-launcher/profiles/<name>/mcp.json"
  claude $_args --dangerously-skip-permissions
}
```

### 5. 删除 Profile

1. 选择要删除的 profile
2. 确认
3. 删除 `~/.cc-launcher/profiles/<name>/` 目录
4. 重新生成 shell 函数

## 注意事项

- `~/.bashrc` 中使用标记（marker）包裹自动生成的内容，避免破坏用户手动配置
- 生成的函数使用 `$HOME` 而非 `~`
- 使用 `test -f` 检测可选文件是否存在
- API Key 存储在 settings.json 中，注意文件权限
