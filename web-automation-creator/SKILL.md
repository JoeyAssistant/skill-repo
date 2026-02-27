---
name: web-automation-creator
description: 通过交互式录制网页操作，生成 Python 自动化脚本。触发场景：(1) "帮我录制网页操作生成脚本" (2) "创建网页自动化脚本" (3) "把这个操作流程自动化" (4) "生成 playwright 自动化脚本"。支持表单填写、数据抓取、通用操作录制。
---

# Web Automation Creator

通过交互式方式记录用户在网页上的操作步骤，生成可复用的 Python 自动化脚本。

## 工作流程

### 步骤 1：收集需求

使用 AskUserQuestion 询问用户：

1. **目标 URL** - 需要自动化的网址
2. **操作描述** - 主要操作内容（表单填写/数据抓取/其他）

### 步骤 2：录制操作

1. 调用 `/playwright-cli` skill 启动浏览器
2. 引导用户逐步完成操作，每步记录：
   - 操作类型（click/input/select/navigate/screenshot/wait）
   - 目标元素选择器（CSS/XPath）
   - 输入值（如有）
   - 操作描述
3. 询问用户是否完成，如未完成则继续录制

### 步骤 3：确认操作列表

用户确认完成后，列出所有记录的操作，格式：

```
操作 1: [类型] [描述] - 选择器: xxx
操作 2: [类型] [描述] - 选择器: xxx
...
```

使用 AskUserQuestion 请用户确认操作列表。

### 步骤 4：确认脚本规格

使用 AskUserQuestion 确认：

1. **脚本名称** - 基于操作总结，与用户确认
2. **输入参数** - 脚本需要的参数（支持 -f/--full 形式）
3. **输出格式** - 默认 JSON，支持 --verbose 打印调试日志

### 步骤 5：生成脚本

生成 Python 脚本，保存到用户指定目录。

## 脚本模板规范

### 文件头格式

```python
#!/usr/bin/env python3
"""
[一句话功能总结]

步骤1：[页面操作描述，关键元素]
步骤2：[页面操作描述，关键元素]
步骤3：[页面操作描述，关键元素]
"""
```

### 参数规范

- 使用 argparse 处理命令行参数
- 每个参数支持短形式（-f）和长形式（--full）
- 默认输出纯 JSON，无额外内容
- --verbose 模式打印调试日志

### 脚本结构

```python
#!/usr/bin/env python3
"""
[功能总结]

步骤1：[描述]
步骤2：[描述]
"""

import argparse
import subprocess
import json
import sys

def run_playwright_cmd(action, *args, verbose=False):
    """执行 playwright CLI 命令"""
    cmd = ["npx", "playwright", action] + list(args)
    if verbose:
        print(f"[DEBUG] Executing: {' '.join(cmd)}", file=sys.stderr)
    result = subprocess.run(cmd, capture_output=True, text=True)
    if verbose:
        print(f"[DEBUG] Output: {result.stdout}", file=sys.stderr)
    return result

def main():
    parser = argparse.ArgumentParser(description="[脚本描述]")
    # 添加参数...
    parser.add_argument("--verbose", action="store_true", help="打印调试日志")

    args = parser.parse_args()

    # 执行自动化操作...
    # 使用 run_playwright_cmd() 调用 playwright CLI

    # 输出结果（JSON 格式）
    print(json.dumps(result, ensure_ascii=False))

if __name__ == "__main__":
    main()
```

## 资源文件

- `assets/script_template.py` - Python 脚本模板
