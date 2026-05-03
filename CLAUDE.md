# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Purpose

This is a collection of custom Claude Code Skills. Skills extend Claude's capabilities with specialized knowledge and workflows.

## Skill Structure

Each skill is a directory containing:
- `SKILL.md` - Main skill definition with YAML frontmatter

```yaml
---
name: skill-name
description: Description with trigger keywords
---
```

## Installing Skills

Local skills are installed by creating symlinks from `~/.claude/skills/<skill-name>` to the skill directory in this repo. Official skills are installed via Claude Code plugins.

## Current Skills

| Skill | Purpose | Trigger |
|-------|---------|---------|
| doc2audio | Web article → Podcast audio | "把文章做成 podcast", "转为音频" |
| note-best-practice | Record best practices | /note-best-practice |
| note-insight | Record insights | /note-insight |
| note-question | Record technical questions | /note-question |
| note-understanding | Record technical understanding | /note-understanding |

## Note-taking Skills

All note skills write to `~/repo/knowledge-notes/[topic]/`:
- `best-practices.md`
- `insights.md`
- `questions.md`
- `understanding.md`

Format: Append with `---` separator between entries.

## doc2audio Dependencies

```bash
pip install edge-tts
# ffmpeg required for audio merging
```

TTS script: `doc2audio/scripts/tts_generator.py`

## Adding New Skills

1. Create directory with skill name
2. Add `SKILL.md` with frontmatter
3. Create symlink: `ln -s $(pwd)/<skill-name> ~/.claude/skills/<skill-name>`
