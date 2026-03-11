---
name: quick-cli
description: 根据结构化数据定义快速生成 CRUD CLI 工具。用于：(1) 用户需要为数据结构创建管理 CLI (2) 用户说"生成一个管理 XX 的 CLI" (3) agent 需要操作结构化数据。支持从 dataclass 文件或交互式描述生成 Python CLI，提供 add/list/get/update/delete 命令，默认 JSON 输出。
---

# Quick CLI

根据 dataclass 定义快速生成 CRUD CLI 工具。

## 工作流程

### 方式一：用户提供 dataclass 文件

1. 展示 dataclass 定义规范（见 [dataclass_guide.md](references/dataclass_guide.md)）
2. 用户提供 schema.py 文件
3. 运行生成脚本
4. 验证生成的 CLI

### 方式二：交互式描述

1. 询问数据结构名称
2. 逐个询问字段：名称、类型、是否必填
3. 生成 dataclass + CLI
4. 验证生成的 CLI

## 生成 CLI

```bash
python scripts/generate_cli.py --schema <schema_file> --output <output_dir>
```

**参数**：
- `--schema`: dataclass schema 文件路径
- `--output`: 输出目录（默认当前目录）
- `--name`: 自定义 CLI 名称（可选）

## 生成的 CLI 使用方式

```bash
# 添加记录
python <name>.py add --field1 "value1" --field2 "value2"

# 列出记录（支持过滤）
python <name>.py list
python <name>.py list --field1 "value1"

# 获取单条
python <name>.py get <id>

# 更新记录（部分更新）
python <name>.py update <id> --field1 "new_value"

# 删除记录
python <name>.py delete <id>

# 指定数据文件
python <name>.py list --data-file /path/to/data.json
```

## 输出格式

- 默认 JSON 输出（agent 友好）
- 错误时输出错误信息，退出码非 0

## 验证流程

生成 CLI 后必须：

1. 运行 `--help` 验证命令结构
2. 执行 add/list/get/update/delete 操作验证功能
3. 确认输出格式正确

## Dataclass 定义规范

详见 [dataclass_guide.md](references/dataclass_guide.md)

**核心规则**：
- 无默认值 = 必填字段
- 有默认值 = 可选字段
- 支持 `str`, `int`, `float`, `bool`, `Enum` 类型
