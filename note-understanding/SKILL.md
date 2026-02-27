---
name: note-understanding
description: 记录技术理解笔记。触发：(1) /note-understanding (2) "记录理解" "add understanding" "技术理解"
---

# Note Understanding

记录技术理解到知识库。

## 快速开始

1. 确定目标目录（默认 ~/repo/knowledge-notes）
2. 遍历现有 topic，选择或创建目录
3. 追加内容到 understanding.md

## 目录结构

```
knowledge-notes/
└── [topic]/
    └── understanding.md
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

用户: "/note-understanding TTS是将文本转为语音的技术"
→ 追加到 knowledge-notes/[topic]/understanding.md

用户: "记录理解：React Hooks 让函数组件拥有状态"
→ 追加到 knowledge-notes/[topic]/understanding.md
