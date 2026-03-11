# Dataclass 定义规范

## 基本规则

| 规则 | 说明 |
|------|------|
| 无默认值 | 必填字段 |
| 有默认值 | 可选字段 |
| `id` 字段 | 自动生成 UUID，无需定义 |

## 支持的字段类型

| 类型 | 示例 | CLI 参数类型 |
|------|------|--------------|
| `str` | `name: str` | 字符串 |
| `int` | `count: int` | 整数 |
| `float` | `price: float` | 浮点数 |
| `bool` | `active: bool` | 布尔值 |
| `Enum` | `status: Status` | 枚举选项 |

## 枚举定义

使用 `str` 和 `Enum` 双重继承：

```python
from enum import Enum

class Status(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    DONE = "done"
```

## 示例

### 简单结构

```python
from dataclasses import dataclass

@dataclass
class Task:
    title: str           # 必填
    description: str = ""  # 可选
    done: bool = False     # 可选
```

### 带枚举的结构

```python
from dataclasses import dataclass
from enum import Enum

class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

@dataclass
class Task:
    title: str
    priority: Priority = Priority.MEDIUM
    done: bool = False
```

### 完整示例

```python
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

class PipelineType(str, Enum):
    CI = "ci"
    CD = "cd"
    BUILD = "build"
    DEPLOY = "deploy"
    TEST = "test"

@dataclass
class Pipeline:
    # 必填字段
    pipeline_name: str
    pipeline_url: str
    project: str
    pipeline_type: PipelineType

    # 可选字段
    module: str = ""
    branch: str = "main"
```
