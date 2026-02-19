---
name: doc2audio
description: 将网页文章转换为音频 Podcast。用于：(1) 用户说"把这个文章做成 podcast" (2) 用户说"将这篇文章转为音频" (3) 用户说"提取这篇文章的内容"。输入为文档或博客的 URL，输出为音频文件。
---

# doc2audio Skill

将网页文章转换为 Podcast 音频文件。

## 输入参数

| 参数 | 必填 | 说明 |
|------|------|------|
| --url | 是 | 文档或博客的 URL 地址 |
| --output | 否 | 输出路径，默认当前目录 |

## 工作流程

### Step 1: 内容抓取（必须使用 Playwright MCP）

使用 Playwright MCP 访问 URL，提取：
- 页面标题 (title)
- 正文原文文本

如果网页无法抓取或无正文，告知用户错误并退出。

### Step 2: 保存原文 MD 文件

根据语言判断：
- 英文原文 → {title}_EN.md
- 中文原文 → {title}_CN.md

### Step 3: 翻译（如需要）

如果原文是英文：
- 调用 LLM 翻译为中文
- 保存 {title}_CN.md

如果原文已是中文：
- 不生成英文版本

### Step 4: Podcast 文本转换

调用 LLM 总结原文内容，生成 Podcast 风格的脚本：
- {title}_EN_podcast.md（如原文为英文）
- {title}_CN_podcast.md

### Step 5: 音频转换

使用 Edge TTS 将 Podcast 文本转为 MP3：
- {title}_EN_podcast.mp3（如生成）
- {title}_CN_podcast.mp3

如超出 Edge TTS 长度限制（6000 字符），自动分段处理。

## TTS 脚本使用

TTS 脚本位置：`doc2audio/scripts/tts_generator.py`

```bash
# 基本用法
python3 doc2audio/scripts/tts_generator.py --text "要转换的文字" --voice "zh-CN-XiaoxiaoNeural" --output "output.mp3"

# 参数说明
# --text, -t: 要转换的文字（必填）
# --voice, -v: 声音名称，默认 zh-CN-XiaoxiaoNeural
# --output, -o: 输出文件路径
# --lang, -l: 语言，en 或 zh-CN，默认 zh-CN
```

可用语音：
- 英文: en-US-JennyNeural
- 中文: zh-CN-XiaoxiaoNeural

## 输出文件

```
{output_dir}/
├── {title}_EN.md           # 英文原文（如有）
├── {title}_CN.md           # 中文翻译（如有）
├── {title}_EN_podcast.md   # English Podcast 文本
├── {title}_CN_podcast.md   # 中文 Podcast 文本
├── {title}_EN_podcast.mp3  # English Podcast 音频（如有）
└── {title}_CN_podcast.mp3  # 中文 Podcast 音频
```

## 使用示例

```bash
# 基本用法
doc2audio --url "https://example.com/article"

# 指定输出目录
doc2audio --url "https://example.com/article" --output "/path/to/output"
```

## 注意事项

- 内容抓取必须使用 Playwright MCP，不能使用 axios/cheerio
- 文件名中的非法字符自动移除
- 如果标题为空，从 URL 提取域名作为标题
