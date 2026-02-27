---
name: note-question
description: 记录技术问题笔记。触发：(1) /note-question (2) "记录问题" "add question" "技术问题"
---

# Note Question

记录技术问题到知识库。

## 快速开始

1. 确定目标目录（默认 ~/repo/knowledge-notes）
2. 遍历现有 topic，选择或创建目录
3. 追加内容到 questions.md

## 目录结构

```
knowledge-notes/
└── [topic]/
    └── questions.md
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

用户: "/note-question TTS是什么？"
→ 追加到 knowledge-notes/[topic]/questions.md

用户: "记录这个问题：如何实现语音合成？"
→ 追加到 knowledge-notes/[topic]/questions.md
