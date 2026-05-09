---
name: ui-design-review
description: Use when building interactive UI review tools with comment/feedback workflow, or when setting up collaborative design iteration loops
---

# UI Design Review Tool

## Overview

Build interactive tools that let users draw regions on UI mockups, leave feedback comments, and generate structured prompts for AI agents to implement changes.

## Core Pattern

```
┌─────────────────────────────────────────────────────────────┐
│                    UI Design Review Tool                     │
├─────────────────────────────┬───────────────────────────────┤
│      Preview Panel            │         Sidebar               │
│   ┌─────────────────────┐     │  ┌─────────────────────────┐ │
│   │  iframe with UI     │     │  │ 💬 Comments (collapsible)│ │
│   │                     │     │  │  - Comment 1 [Pending]  │ │
│   │   [overlay for      │     │  │  - Comment 2 [Resolved] │ │
│   │    drawing boxes]   │     │  └─────────────────────────┘ │
│   │                     │     │  ┌─────────────────────────┐ │
│   └─────────────────────┘     │  │ 📋 Prompt (collapsible)│ │
│                               │  │  [structured output]    │ │
│                               │  └─────────────────────────┘ │
└─────────────────────────────┴───────────────────────────────┘
```

## Layout Structure

```html
<!-- 3-panel layout: header + content + bottom prompt -->
<div class="app">
  <header class="header">...</header>
  <div class="content">
    <div class="preview-panel">  <!-- flex: 1, scrollable -->
      <iframe src="target-page.html"/>
      <div class="draw-overlay"/>  <!-- absolute positioned over iframe -->
    </div>
    <div class="sidebar" id="sidebar">  <!-- collapsible 320px → 44px -->
      <div class="sidebar-header" id="sidebarToggle">...</div>
      <div class="sidebar-content">...</div>
    </div>
  </div>
  <div class="prompt-panel">...</div>  <!-- fixed height, collapsible -->
</div>
```

## Key Implementation Details

### 1. Scroll Sync (Critical)
Without scroll sync, drawing breaks when preview scrolls:

```javascript
// Sync overlay scroll with container
previewContainer.addEventListener('scroll', () => {
  overlay.scrollTop = previewContainer.scrollTop;
  overlay.scrollLeft = previewContainer.scrollLeft;
});
```

### 2. Collapsible Sidebar
```css
.sidebar {
  width: 320px;
  transition: width 0.3s ease;
}
.sidebar.collapsed {
  width: 44px;  /* Keep toggle visible, hide content */
}
.sidebar.collapsed .sidebar-content {
  display: none;
}
```

### 3. Drawing Rectangle Logic
```javascript
let isDrawing = false;
let drawStart = null;

overlay.addEventListener('mousedown', (e) => {
  if (mode !== 'draw') return;
  isDrawing = true;
  drawStart = { x: e.clientX - rect.left, y: e.clientY - rect.top };
});

overlay.addEventListener('mouseup', (e) => {
  if (!isDrawing) return;
  isDrawing = false;
  // Create comment from drawn rectangle
  comments.push({
    id: Date.now(),
    number: comments.length + 1,
    x: Math.min(startX, endX),
    y: Math.min(startY, endY),
    width: Math.abs(endX - startX),
    height: Math.abs(endY - startY),
    text: '',
    resolved: false
  });
});
```

### 4. State Structure
```javascript
const state = {
  mode: 'view',      // 'view' or 'draw'
  comments: [],       // { id, number, x, y, width, height, text, resolved }
  sidebarCollapsed: false,
  promptCollapsed: false
};
```

### 5. CSS Variables (Design System)
```css
:root {
  --bg-deep: #0c0e14;
  --bg-primary: #111420;
  --bg-card: #181c28;
  --accent: #c9a96e;
  --accent-dim: rgba(201,169,110,0.15);
  --text-primary: #e8e4df;
  --text-secondary: #8b8d97;
  --border-subtle: rgba(255,255,255,0.04);
  --green: #6ecf8e;
  --red: #e06c6c;
  --amber: #e8a86d;
  --radius: 12px;
  --radius-sm: 8px;
}
```

## Quick Reference

| Feature | Implementation |
|---------|---------------|
| Draw mode toggle | Toggle `.draw-overlay.active` class |
| Create comment | On mouseup, push to `state.comments` |
| Prompt generation | Filter comments with `text.trim()` then format |
| Collapse sidebar | Toggle `.sidebar.collapsed` + `.sidebar-content { display: none }` |
| Collapse prompt | Toggle `.prompt-content.collapsed` class |

## Common Mistakes

1. **Missing scroll sync** - Drawing coordinates wrong when overlay scrolled
2. **Using `overflow: hidden` on container** - Prevents iframe scrolling
3. **Collapsing to `width: 0`** - Can't click toggle to expand again, use `width: 44px`
4. **Prompt requires text** - Only comments with `text.trim()` generate prompt output

## Real-World Impact

Built: http://localhost:8765/doc/frontend/ui-review-playground.html

Verified features:
- ✅ Draw rectangles on iframe preview
- ✅ Create comments with numbers
- ✅ Fill comment text → generates prompt
- ✅ Sidebar collapse/expand
- ✅ Prompt collapse/expand
- ✅ Resolve comments
- ✅ Copy prompt to clipboard