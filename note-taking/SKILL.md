---
name: note-taking
description: 用于记录工作、开发、学习过程中的知识点、理解与感悟。支持四种笔记类型：questions(技术问题)、understanding(技术理解)、best-practices(最佳实践)、insights(感悟)。触发关键字：add question、add understanding、add best practices、add insights。当用户要求记录知识点、创建笔记、保存理解或记录感悟时触发，也可用于自动记录回答中的知识点。
---

# Note Taking

## 快速开始

用户要求记录笔记时：
1. 确定目标目录（默认 ~/knowledge-notes，如不存在则询问用户）
2. 遍历现有 topic，优先使用已存在的目录
3. 确定笔记类型（questions/understanding/best-practices/insights）
4. 追加内容到对应文件

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

| 类型 | 文件 | 触发关键字 |
|------|------|------------|
| 技术问题 | questions.md | add question |
| 技术理解 | understanding.md | add understanding |
| 最佳实践 | best-practices.md | add best practices |
| 感悟 | insights.md | add insights |

## 使用流程

1. **获取目录路径**
   - 默认使用 ~/knowledge-notes
   - 如目录不存在，询问用户

2. **确定 topic**
   - 遍历现有 topic 目录，列出已有 topics
   - 优先使用已存在的 topic 目录
   - 新建 topic 目录需要用户显式确认

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
