# Doc Review Skill v2 Design

**Date**: 2026-05-30
**Status**: Approved

## Problem Statement

The current doc-review skill has three issues:

1. **Slow generation** — AI generates 3-7 suggestions per round, requiring expensive LLM calls and complex JSON construction
2. **Low suggestion adoption** — Users rarely accept AI-generated suggestions, making the generation step wasteful
3. **Poor reading experience** — Dark theme, monospace font, code-editor style UI is not suitable for document reading

## Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| AI suggestions | **Remove entirely** | Low adoption, biggest performance bottleneck |
| Interaction flow | **Keep prompt loop** | User comments → copy prompt → paste back → apply → rebuild |
| Visual theme | **Light reading mode** | Notion/Typora style, white background, good typography |
| Layout | **Split panel** | Left: document (70%), Right: comment list (30%) |
| Document rendering | **Markdown live rendering** | marked.js + highlight.js, with line numbers preserved |
| Comment UI | **Right panel input** | Click doc line → right panel shows input, comment list always visible |
| Mermaid support | **Keep, inlined** | 3MB mermaid.min.js inlined into HTML for offline use |
| Headless server | **Preserve** | Python HTTP server for headless Linux environments |

## Architecture

### File Changes

```
doc-review/
├── SKILL.md                          # REWRITE: 4-step simplified flow
├── references/
│   ├── review-template.html          # REWRITE: new light theme + layout
│   ├── playground-template.md        # DELETE: no longer needed
│   ├── mermaid.min.js                # KEEP: unchanged
│   ├── marked.min.js                 # ADD: Markdown renderer (~30KB)
│   └── highlight.min.js              # ADD: Code syntax highlighter (~50KB)
├── scripts/
│   └── build-review-html.js          # SIMPLIFY: no suggestion validation
└── docs/superpowers/specs/
    └── 2026-05-30-doc-review-v2-design.md  # This file
```

### New SKILL.md Flow (4 steps, down from 7)

```
Step 1: Build HTML playground
  - Read the target document
  - Generate JSON with Python (only docPath + docLines + round, no suggestions)
  - Run build script with --serve flag

Step 2: Wait for user feedback
  - User adds comments in browser
  - User copies prompt and pastes back
  - "继续" → skip to Step 4

Step 3: Apply changes
  - Parse "My Comments" from pasted prompt
  - Apply each comment using Edit tool or Python fallback
  - Cross-reference check for renames

Step 4: Rebuild playground
  - Re-read updated document
  - Delete stale review HTML files
  - Rebuild JSON + HTML with --serve
  - Return to Step 2

Completion: User says "确认完成" → delete temp files, exit
```

### JSON Schema (simplified)

```json
{
  "docPath": "path/to/doc.md",
  "round": 1,
  "docLines": ["line1", "line2", "..."]
}
```

No more `suggestions` array, no more `targetLineStart/targetLineEnd/targetText`.

### HTML Template Structure

```
┌─────────────────────────────────────────────────┐
│ Header: 文档名 | Round N | 提示 | Comment 统计   │
├──────────────────────┬──────────────────────────┤
│                      │                          │
│   文档面板 (70%)      │   评论面板 (30%)          │
│   Markdown 渲染      │   Comment 列表            │
│   保留行号           │   输入区（点击行激活）     │
│   点击行 → 右侧激活  │   编辑/删除按钮           │
│                      │                          │
├──────────────────────┴──────────────────────────┤
│ Prompt 面板（可折叠）                             │
│ [Copy] 按钮 | Prompt 文本内容                     │
└─────────────────────────────────────────────────┘
```

### Visual Theme — Light Reading Mode

- **Background**: White `#ffffff`, sidebar `#f8f9fa`
- **Text**: Dark gray `#1f2937`, secondary `#6b7280`
- **Accent**: Blue `#3b82f6` (comments), Green `#10b981` (confirm)
- **Typography**: Sans-serif 15px body, headings 26/20/16px, line-height 1.7
- **Code blocks**: Dark background `#1f2937` + highlight.js syntax highlighting
- **Comment cards**: White cards with left blue border
- **Hover state**: Light blue background + blue left border on doc lines

### JavaScript Architecture

```javascript
// State management
const state = {
  comments: [],      // { id, lineNum, text }
  nextId: 1,
  editingLine: null,
};

// Event delegation (not per-element binding)
docPanel.addEventListener('click', handleDocClick);
commentList.addEventListener('click', handleCommentClick);
```

Key difference from v1: **Event delegation** on containers instead of per-element listeners. This prevents bugs when `renderDocument()` destroys and recreates DOM elements.

### Prompt Engineering Improvements (from Google's whitepaper)

Applied to SKILL.md:

| Principle | Application |
|-----------|-------------|
| Design with simplicity | 7 steps → 4 steps |
| Be specific about output | Clear JSON schema, explicit build command |
| Instructions over constraints | "Use Python to generate JSON" instead of "Don't manually write JSON" |
| Use variables | Parameterized template with clear fill markers |
| Provide examples | Include example Python script in SKILL.md |

### Libraries

| Library | Size | Purpose | Loading |
|---------|------|---------|---------|
| marked.js | ~30KB | Markdown rendering | Inlined by build script |
| highlight.js | ~50KB | Code syntax highlighting | Inlined by build script |
| mermaid.min.js | ~3MB | Mermaid diagram rendering | Inlined by build script (kept from v1) |

All libraries are inlined into the single HTML file for offline use. No CDN dependencies.

### Preserved Features

- **Headless server mode**: `serveWithPython()` function in build script, auto-detects macOS/Linux GUI/headless
- **Mermaid rendering**: mermaid.min.js inlined, `mermaid.run()` called after document render
- **Prompt generation**: Auto-generates prompt from user comments with line references
- **Copy to clipboard**: With fallback for non-secure contexts
- **Keyboard shortcuts**: `Esc` cancel, `Ctrl+Enter` save
- **Round tracking**: Round number displayed and incremented

### Removed Features

- AI suggestion generation (the entire Step 1 in v1)
- Suggestion approve/reject/reset buttons
- Suggestion filter tabs (All/Pending/Approved/Rejected/My Comments)
- Suggestion status badges and state management
- Suggestion targetText validation in build script
- playground-template.md (reference doc for the old template)
- mermaid min.js for the mermaid rendering (kept but simplified integration)

## Out of Scope

- Dark/light theme toggle (YAGNI — light mode only)
- Comment threading or replies
- Multi-line comment ranges (keep simple: one comment per line)
- Document diff view between rounds
- Export to PDF or other formats
