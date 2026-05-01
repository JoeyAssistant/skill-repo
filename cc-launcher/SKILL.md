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

1. 检测当前平台（`uname` / `$env:OS`）
2. 扫描所有 `~/.cc-launcher/profiles/*/settings.json`
3. 为每个 profile 生成两个 shell function：
   - `claude-<name>()` — 正常模式
   - `claude-<name>-skip-perms()` — 跳过权限模式
4. 函数使用 `--settings`、`--append-system-prompt-file`、`--mcp-config` 参数
5. 根据平台写入对应的配置文件（见下方模板），替换标记之间的内容
6. 如果标记不存在，追加到文件末尾

**标记（Marker）：**
- `# >>> Claude Code profiles - start >>>` / `# <<< Claude Code profiles - end <<<`

**平台适配：**
| 平台 | 配置文件 | 路径 |
|------|----------|------|
| Linux/macOS (bash) | `~/.bashrc` | `$HOME/.cc-launcher/profiles/<name>/` |
| Windows (PowerShell) | `$PROFILE` | `$HOME/.cc-launcher/profiles/<name>/` |

Bash 函数模板（Linux/macOS）：

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

PowerShell 函数模板（Windows）：

```powershell
function claude-<name> {
  $profileDir = "$HOME/.cc-launcher/profiles/<name>"
  $args = @("--settings", "$profileDir/settings.json")
  if (Test-Path "$profileDir/system-prompt.md") { $args += @("--append-system-prompt-file", "$profileDir/system-prompt.md") }
  if (Test-Path "$profileDir/mcp.json") { $args += @("--mcp-config", "$profileDir/mcp.json") }
  claude @args
}

function claude-<name>-skip-perms {
  $profileDir = "$HOME/.cc-launcher/profiles/<name>"
  $args = @("--settings", "$profileDir/settings.json")
  if (Test-Path "$profileDir/system-prompt.md") { $args += @("--append-system-prompt-file", "$profileDir/system-prompt.md") }
  if (Test-Path "$profileDir/mcp.json") { $args += @("--mcp-config", "$profileDir/mcp.json") }
  claude @args --dangerously-skip-permissions
}
```

**写入 PowerShell $PROFILE 的步骤：**
1. 检查 `$PROFILE` 文件是否存在，不存在则创建（含父目录）
2. 读取 `$PROFILE` 内容，定位标记区域
3. 替换标记间内容，或追加到末尾
4. 提示用户运行 `. $PROFILE` 或重启终端以生效

### 5. 删除 Profile

1. 选择要删除的 profile
2. 确认
3. 删除 `~/.cc-launcher/profiles/<name>/` 目录
4. 重新生成 shell 函数

## 注意事项

- 配置文件（`.bashrc` / `$PROFILE`）中使用标记（marker）包裹自动生成的内容，避免破坏用户手动配置
- 生成的函数使用 `$HOME` 而非 `~`
- Bash 使用 `test -f`，PowerShell 使用 `Test-Path` 检测可选文件是否存在
- PowerShell 的 `$PROFILE` 路径通常为 `~\Documents\PowerShell\Microsoft.PowerShell_profile.ps1`
- Windows 上 PowerShell 函数名中的 `-` 是合法字符，无需特殊处理
- API Key 存储在 settings.json 中，注意文件权限
