---
name: note-best-practice
description: 记录最佳实践笔记。触发：(1) /note-best-practice (2) "记录最佳实践" "add best practices" "best practice"
---

# Note Best Practice

记录最佳实践到知识库。

## 快速开始

1. 确定目标目录（默认 ~/repo/knowledge-notes）
2. 遍历现有 topic，选择或创建目录
3. 追加内容到 best-practices.md

## 目录结构

```
knowledge-notes/
└── [topic]/
    └── best-practices.md
```

## 使用流程

1. **获取目录路径** - 默认 ~/repo/knowledge-notes
2. **确定 topic** - 列出已有 topics，优先使用已存在的
3. **追加内容** - 末尾添加，用 `---` 分隔

## 笔记格式

```markdown
---

### [标题]

[内容]
```

## 示例

用户: "/note-best-practice 写代码前先写测试"
→ 追加到 knowledge-notes/[topic]/best-practices.md

用户: "记录最佳实践：使用语义化版本号"
→ 追加到 knowledge-notes/[topic]/best-practices.md
