---
name: note-insight
description: 记录感悟笔记。触发：(1) /note-insight (2) "记录感悟" "add insights" "感悟"
---

# Note Insight

记录感悟到知识库。

## 快速开始

1. 确定目标目录（默认 ~/repo/knowledge-notes）
2. 遍历现有 topic，选择或创建目录
3. 追加内容到 insights.md

## 目录结构

```
knowledge-notes/
└── [topic]/
    └── insights.md
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

用户: "/note-insight AI改变了编程方式"
→ 追加到 knowledge-notes/[topic]/insights.md

用户: "记录感悟：简单的设计往往更可靠"
→ 追加到 knowledge-notes/[topic]/insights.md
