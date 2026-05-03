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
  - `settings.json` — env + 模型 + 启用的插件
  - `mcp.json` — MCP 服务器配置（可选）
  - `system-prompt.md` — 系统提示词（可选）

## settings.json 格式

```json
{
  "env": {
    "ANTHROPIC_AUTH_TOKEN": "<api_key>",
    "ANTHROPIC_BASE_URL": "<base_url>",
    "ANTHROPIC_DEFAULT_HAIKU_MODEL": "<model>",
    "ANTHROPIC_DEFAULT_SONNET_MODEL": "<model>",
    "ANTHROPIC_DEFAULT_OPUS_MODEL": "<model>"
  },
  "model": "sonnet",
  "enabledPlugins": {
    "plugin-name@marketplace": true
  },
  "tools": {
    "mmx": {}
  }
}
```

**要点：**
- 插件使用 `enabledPlugins`（对象，值为 boolean），**不是** `plugins`（数组）
- 模型映射通过环境变量 `ANTHROPIC_DEFAULT_*_MODEL` 实现，**不是** `modelMap` 字段
- `model` 字段填 Claude 模型级别（如 `"sonnet"`），实际模型名由环境变量决定

## mcp.json 格式

```json
{
  "mcpServers": {
    "<name>": {
      "type": "http | stdio",
      "url": "<http 类型必填>",
      "headers": { "Authorization": "Bearer <key>" },
      "command": "<stdio 类型必填>",
      "args": ["<stdio 类型>"],
      "env": { "<stdio 类型>": "<value>" }
    }
  }
}
```

**MCP 分配策略：**
- 按 API Key 归属分配到对应 profile（如智谱 MCP → GLM profile，MiniMax MCP → MiniMax profile）
- stdio 类型（如 npx 启动的本地 MCP）需指定 `command`、`args`、`env`
- http 类型（远程 MCP）需指定 `url`、`headers`

## 插件安装流程

启用第三方 marketplace 的插件前，必须完成以下步骤：

1. **克隆 marketplace** 到 `~/.claude/plugins/marketplaces/<name>/`
2. **注册 marketplace** 到 `~/.claude/plugins/known_marketplaces.json`：
   ```json
   {
     "<marketplace-name>": {
       "source": { "source": "github", "repo": "<org>/<repo>" },
       "installLocation": "<path>",
       "lastUpdated": "<ISO datetime>"
     }
   }
   ```
3. **安装插件**到缓存 `~/.claude/plugins/cache/<marketplace>/<plugin>/<version>/`
4. **注册插件**到 `~/.claude/plugins/installed_plugins.json`：
   ```json
   {
     "<plugin>@<marketplace>": [{
       "scope": "user",
       "installPath": "<cache path>",
       "version": "<version>",
       "installedAt": "<ISO datetime>",
       "lastUpdated": "<ISO datetime>"
     }]
   }
   ```
5. **在 profile 的 `enabledPlugins` 中启用**：`"<plugin>@<marketplace>": true`

## 操作流程

### 1. 创建 Profile

1. 读取 `providers.json`，展示已知供应商列表
2. 用户选择供应商（或输入自定义名称）
3. 如果是已知供应商且有 `doc_url`，使用 web fetch 抓取文档，提取默认配置（base_url、模型名等）
4. 交互式收集：
   - API Key（ANTHROPIC_AUTH_TOKEN）
   - **安装供应商 CLI 工具**：如果 `providers.json` 中该供应商有 `tools` 字段（如 MiniMax 的 mmx），则执行安装
     - MiniMax：执行 `pip install mmx-cli` 安装 mmx
   - 确认/修改 base_url、模型映射
   - 从 `registry.json` 选择插件（预选 universal + 匹配 providers 的条目）
   - 系统提示词（可选）：使用 `providers.json` 中的 `systemPromptTemplate`，包含 mmx 使用说明
   - MCP 配置（可选）
5. 生成 profile 文件到 `~/.cc-launcher/profiles/<name>/`
   - `settings.json` 中添加 `"tools": { "mmx": {} }` 标记已安装的工具
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

1. 检测当前平台和 shell（`echo $SHELL` / `$env:SHELL` / `uname`）
2. 扫描所有 `~/.cc-launcher/profiles/*/settings.json`
3. 为每个 profile 生成两个 shell function：
   - `claude-<name>()` — 正常模式
   - `claude-<name>-skip-perms()` — 跳过权限模式
4. 函数使用 `--settings`、`--append-system-prompt-file`、`--mcp-config` 参数
5. 函数**必须转发用户参数 `"$@"` / `@PSBoundParameters`**，否则用户传入的额外参数（如 `--append-system-prompt`）会被丢弃
6. 根据平台写入对应的配置文件（见下方模板），替换标记之间的内容
7. 如果标记不存在，追加到文件末尾

**标记（Marker）：**
- Bash/Zsh：`# >>> Claude Code profiles - start >>>` / `# <<< Claude Code profiles - end <<<`
- PowerShell：`# >>> Claude Code profiles - start >>>` / `# <<< Claude Code profiles - end <<<`

**平台适配：**
| 平台 | Shell | 配置文件 | 检测方式 |
|------|-------|----------|----------|
| macOS | zsh | `~/.zshrc` | `$SHELL` 含 `zsh` 或 macOS 默认 |
| macOS | bash | `~/.bash_profile` | `$SHELL` 含 `bash` |
| Linux | bash | `~/.bashrc` | `$SHELL` 含 `bash` |
| Linux | zsh | `~/.zshrc` | `$SHELL` 含 `zsh` |
| Windows | PowerShell | `$PROFILE` | N/A |

**平台检测逻辑：**
1. 读取 `$SHELL` 环境变量（Unix）或 `$env:SHELL`（PowerShell）
2. 如果 `$SHELL` 包含 `zsh` → 写入 `~/.zshrc`
3. 如果 `$SHELL` 包含 `bash` → 写入 `~/.bashrc`（Linux）或 `~/.bash_profile`（macOS）
4. 如果在 PowerShell 中 → 写入 `$PROFILE`

Bash/Zsh 函数模板（Linux/macOS）：

```bash
claude-<name>() {
  local -a _args=("--settings" "$HOME/.cc-launcher/profiles/<name>/settings.json")
  test -f "$HOME/.cc-launcher/profiles/<name>/system-prompt.md" && _args+=("--append-system-prompt-file" "$HOME/.cc-launcher/profiles/<name>/system-prompt.md")
  test -f "$HOME/.cc-launcher/profiles/<name>/mcp.json" && _args+=("--mcp-config" "$HOME/.cc-launcher/profiles/<name>/mcp.json")
  claude "${_args[@]}" "$@"
}

claude-<name>-skip-perms() {
  local -a _args=("--settings" "$HOME/.cc-launcher/profiles/<name>/settings.json")
  test -f "$HOME/.cc-launcher/profiles/<name>/system-prompt.md" && _args+=("--append-system-prompt-file" "$HOME/.cc-launcher/profiles/<name>/system-prompt.md")
  test -f "$HOME/.cc-launcher/profiles/<name>/mcp.json" && _args+=("--mcp-config" "$HOME/.cc-launcher/profiles/<name>/mcp.json")
  claude "${_args[@]}" "$@" --dangerously-skip-permissions
}
```

**Bash/Zsh 模板要点：**
- 使用 `local -a _args=(...)` 数组，**不是**字符串拼接 — 避免路径含空格时出错
- 使用 `_args+=("--flag" "$value")` 追加元素，**不是** `$_args="$_args --flag $value"`
- `"${_args[@]}"` 带引号展开数组，**不是** `$_args`
- 末尾加 `"$@"` 转发用户参数 — 这是必须的，否则 `claude-glm --append-system-prompt "..."` 等调用会静默失败

PowerShell 函数模板（Windows）：

```powershell
function claude-<name> {
  $profileDir = "$HOME\.cc-launcher\profiles\<name>"
  $claudeArgs = @("--settings", "$profileDir\settings.json")
  if (Test-Path "$profileDir\system-prompt.md") { $claudeArgs += @("--append-system-prompt-file", "$profileDir\system-prompt.md") }
  if (Test-Path "$profileDir\mcp.json") { $claudeArgs += @("--mcp-config", "$profileDir\mcp.json") }
  claude @claudeArgs @PSBoundParameters.Values
}

function claude-<name>-skip-perms {
  $profileDir = "$HOME\.cc-launcher\profiles\<name>"
  $claudeArgs = @("--settings", "$profileDir\settings.json")
  if (Test-Path "$profileDir\system-prompt.md") { $claudeArgs += @("--append-system-prompt-file", "$profileDir\system-prompt.md") }
  if (Test-Path "$profileDir\mcp.json") { $claudeArgs += @("--mcp-config", "$profileDir\mcp.json") }
  $claudeArgs += "--dangerously-skip-permissions"
  claude @claudeArgs @PSBoundParameters.Values
}
```

**PowerShell 模板要点：**
- 变量名用 `$claudeArgs`，**不是** `$args` — `$args` 是 PowerShell 自动变量，覆盖它会导致不可预测的行为
- `--dangerously-skip-permissions` 追加到 `$claudeArgs` 数组内，**不是**放在 `claude @claudeArgs` 后面 — PowerShell 的 splatting `@array` 之后不能追加位置参数
- 使用 `@PSBoundParameters.Values` 转发用户传入的参数

**写入配置文件的步骤：**
1. 检查配置文件是否存在，不存在则创建（含父目录）
2. 读取配置文件内容，定位标记区域
3. 替换标记间内容，或追加到文件末尾
4. 提示用户 `source ~/.zshrc`（或对应配置文件）或重启终端以生效

### 5. 删除 Profile

1. 选择要删除的 profile
2. 确认
3. 删除 `~/.cc-launcher/profiles/<name>/` 目录
4. 重新生成 shell 函数

## 注意事项

- 配置文件（`~/.zshrc` / `~/.bashrc` / `$PROFILE`）中使用标记（marker）包裹自动生成的内容，避免破坏用户手动配置
- 生成的函数使用 `$HOME` 而非 `~`
- Bash/Zsh 使用 `test -f`，PowerShell 使用 `Test-Path` 检测可选文件是否存在
- **Bash/Zsh 函数必须使用数组 `local -a` + `"${_args[@]}"`**，不要用字符串拼接 — 字符串方式遇到路径空格会 break，且无法正确转发 `"$@"`
- **函数末尾必须加 `"$@"` 转发用户参数**，否则 `claude-<name> --append-system-prompt "..."` 等调用会被静默丢弃
- PowerShell 的 `$PROFILE` 路径通常为 `~\Documents\PowerShell\Microsoft.PowerShell_profile.ps1`
- PowerShell 变量名**不要**用 `$args`（自动变量），用 `$claudeArgs` 等自定义名称
- PowerShell 的 splatting `@array` 后不能追加位置参数，必须将所有参数放入数组
- Windows 上 PowerShell 函数名中的 `-` 是合法字符，无需特殊处理
- API Key 存储在 settings.json 中，注意文件权限
