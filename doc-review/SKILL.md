---
name: doc-review
description: Use when the user needs to review a document, design spec, or any text artifact and wants to provide structured feedback through an interactive playground. Triggers include "review this doc", "我来review", "帮我看看这个文档", generating a document that needs user approval before finalizing, or any iterative document review workflow. Also use after generating a design doc, data schema, API spec, or similar artifact that requires user sign-off. Make sure to use this skill whenever a document needs human review and feedback, even if the user doesn't explicitly ask for a "review".
---

# Interactive Document Review

## Overview

Generate an interactive HTML playground for reviewing documents. The user reviews in a browser, approves/rejects AI suggestions, adds inline comments on any line, then pastes a generated prompt back for Claude to apply changes. Loop until confirmed.

## Key Principles

1. **User is in control**: The user decides when the review is complete, not the AI. Never assume "OK" — always wait for explicit confirmation.
2. **Preview before destructive changes**: For major structural changes (deleting sections, rewriting content), show a preview first.

## Step-by-step

### 1. Analyze and generate suggestions

Read the target document. Generate 3-7 review suggestions per round (fewer if doc is short/clean).

**Suggestion quality guidelines:**
- Reference specific line numbers, not vague sections
- Be actionable: state what's wrong AND what to do about it
- Focus on real issues, not cosmetic preferences
- Cross-check consistency between sections
- Categories: `clarity` | `completeness` | `consistency` | `correctness`

### 2. Build the playground

Write a JSON file and run the build script. **Do NOT manually construct HTML.**

1. Write a JSON file to `<doc-dir>/<doc-name>-review.json`:

```json
{
  "docPath": "path/to/doc.md",
  "round": 1,
  "docLines": ["line1", "line2", "..."],
  "suggestions": [
    {
      "id": "a1",
      "lineRef": "Line 5-27",
      "targetLineStart": 5,
      "targetLineEnd": 27,
      "targetText": "first ~60 chars of target content",
      "suggestion": "what to improve and why",
      "category": "clarity"
    }
  ]
}
```

2. Run the build script:

```bash
node ~/.claude/skills/doc-review/scripts/build-review-html.js <doc-dir>/<doc-name>-review.json
```

The script outputs `<doc-name>-review.html` in the same directory with built-in validation (JS syntax + line count).

3. Open in browser: `open <doc-dir>/<doc-name>-review.html`

### 3. Wait for user feedback

The user reviews in the browser and either:
- Pastes the generated prompt back (has approved suggestions and/or user comments)
- Gives explicit completion confirmation

**IMPORTANT**: Do NOT interpret any response as final confirmation unless the user explicitly says so. If the user says things like "继续review" or "再看看", continue the review loop.

**Keywords that mean "continue"** (immediate rebuild, no confirmation check):
- "继续"、"继续review"、"再来"、"再看看"、"继续看"
- Any response that doesn't contain "确认完成"、"可以了"、"没问题"

When user says "继续" or similar, skip to Step 6 immediately — do not ask any questions.

### 4. Preview before applying changes

For any "My Comments" or structural changes, BEFORE applying:
1. Read the proposed changes
2. If the changes are significant (deleting sections, rewriting substantial content), summarize what will change and ask: "我将应用以下修改，是否确认？"
3. Wait for explicit user confirmation before modifying the document

### 5. Apply changes

Parse the user's pasted prompt and apply each change to the document. Changes fall into three categories:

| Section in prompt | Action |
|-------------------|--------|
| Approved Improvements | Apply the suggestion |
| My Comments | Apply the user's comment as instruction |
| Rejected | Skip (listed for context only) |

### 6. Rebuild playground

After applying changes:
1. Re-read the updated document
2. Generate new suggestions (don't repeat already-addressed items)
3. **Before generating new HTML, delete any existing review HTML in the doc directory** — stale files cause "内容为空" bugs
4. Write updated JSON and re-run the build script
5. Open in browser

If no new suggestions are warranted, write JSON with an empty `suggestions` array — the playground will show: "No items match this filter" and the user can still add inline comments.

### 7. Explicit confirmation check

Ask the user to explicitly choose one of two actions:

```
本次 review 完成了吗？
- 如果还需要修改 → 告诉我具体内容，我会继续
- 如果已完成 → 说"确认完成"，我会删除临时文件并结束
```

**Only these phrases trigger cleanup and exit:**
- "确认完成"、"可以了"、"没问题"、"完成了"

**Everything else is "continue":**
- "继续"、"再看看"、"还需要改"、"还没完"等任何非完成确认
- If user says anything other than explicit completion phrases, rebuild and continue (Step 6)

Repeat steps 3-6 until user explicitly confirms completion.

## When NOT to use this skill

- Simple typo fixes or one-line changes (just edit directly)
- Documents the user is still actively drafting (review comes after drafting)
- Non-text artifacts (images, binary files)
