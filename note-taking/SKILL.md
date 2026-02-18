---
name: note-taking
description: 用于记录工作、开发、学习过程中的知识点、理解与感悟。支持四种笔记类型：questions(技术问题)、understanding(技术理解)、best-practices(最佳实践)、insights(感悟)。当用户要求记录知识点、创建笔记、保存理解或记录感悟时触发，也可用于自动记录回答中的知识点。
---

# Note Taking

## 快速开始

用户要求记录笔记时：
1. 获取目标目录路径（用户指定或询问）
2. 确定 topic 名称
3. 确定笔记类型（questions/understanding/best-practices/insights）
4. 追加内容到对应文件的对应 section

## 目录结构

```
knowledge-notes/
└── [topic]/
    ├── questions.md        # 技术问题
    ├── understanding.md   # 技术理解
    ├── best-practices.md  # 最佳实践
    └── insights.md        # 感悟
```

## 笔记类型

| 类型 | 文件 | 触发方式 |
|------|------|----------|
| 技术问题 | questions.md | "记录这个问题"、"什么是XXX" |
| 技术理解 | understanding.md | "记录这个知识点"、"理解是..." |
| 最佳实践 | best-practices.md | "记录这个 best practice" |
| 感悟 | insights.md | "记录感悟"、"记下这个想法" |

## 使用流程

1. **获取目录路径**
   - 用户明确指定：直接使用
   - 未指定：询问用户

2. **确定 topic**
   - 根据内容主题确定 topic 名称
   - topic 不存在则创建完整目录结构

3. **追加内容**
   - 打开对应的 .md 文件
   - 在末尾添加新内容，用 `---` 分隔
   - 使用简洁的 Markdown 格式

## 笔记格式

```markdown
---

### [标题]

[简短内容]

```

## 示例

用户说 "记录这个问题：TTS是什么？"
→ 追加到 `knowledge-notes/[topic]/questions.md`:

```markdown
---

### TTS是什么？

TTS (Text-to-Speech) 是文本转语音技术...

```

用户说 "记录感悟：在AI加持下，编码可以不需要人类了"
→ 追加到 `knowledge-notes/[topic]/insights.md`:

```markdown
---

### AI时代的编程

在当前AI技术的加持下，今后的编码可以不需要由人类执行了...

```
