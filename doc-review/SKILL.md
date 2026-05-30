---
name: doc-review
description: Use when the user needs to review a document, design spec, or any text artifact and wants to provide structured feedback through an interactive playground. Triggers include "review this doc", "我来review", "帮我看看这个文档", generating a document that needs user approval before finalizing, or any iterative document review workflow. Also use after generating a design doc, data schema, API spec, or similar artifact that requires user sign-off.
---

# Interactive Document Review

Generate an interactive HTML playground for reviewing documents. The user reviews in a browser, adds inline comments on any line, copies the generated prompt, and pastes it back for Claude to apply changes. Loop until confirmed.

## Principles

1. **User is in control** — the user decides when the review is complete. Never assume "OK" — always wait for explicit confirmation.
2. **Preview before destructive changes** — for major structural changes (deleting sections, rewriting content), show a preview first.

## Step-by-step

### 1. Build the playground

Read the target document. Use Python to generate a JSON file, then run the build script.

```bash
python3 -c "
import json
with open('<doc-path>', 'r') as f:
    lines = f.read().splitlines()

data = {
    'docPath': '<doc-path>',
    'round': 1,
    'docLines': lines
}
with open('<doc-dir>/<doc-name>-review.json', 'w') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
print(f'JSON ready: {len(lines)} lines')
"
```

Then run the build script:

```bash
node ~/.claude/skills/doc-review/scripts/build-review-html.js --serve <doc-dir>/<doc-name>-review.json
```

The script outputs `<doc-name>-review.html` in the same directory.

The `--serve` flag auto-detects the environment:
   - **macOS**: opens in browser with `open`
   - **Linux with GUI** (`$DISPLAY` + `xdg-open`): opens in browser with `xdg-open`
   - **Headless Linux**: starts a Python HTTP server, prints the URL to access from your local browser

### 2. Wait for user feedback

The user reviews in the browser and either:
- Pastes the generated prompt back (has comments to apply)
- Gives explicit completion confirmation

**Keywords that mean "continue"** (skip confirmation check, go to Step 4):
- "继续"、"继续review"、"再来"、"再看看"、"继续看"
- Any response that doesn't contain "确认完成"、"可以了"、"没问题"

When user says "继续", skip to Step 4 immediately.

### 3. Apply changes

Parse the user's pasted prompt and apply each "My Comments" entry to the document.

**Applying strategy — Edit tool vs Python fallback:**

Prefer the Edit tool for small, unique string replacements. When Edit fails twice on the same block, switch to Python line-number replacement:

```bash
python3 << 'PYEOF'
with open('<doc-path>', 'r', encoding='utf-8') as f:
    lines = f.readlines()
start = None
end = None
for i, line in enumerate(lines):
    if '<unique marker>' in line: start = i
    if start is not None and '<end marker>' in line: end = i; break
new_lines = ['### New Content\n', '\n']
lines[start:end+1] = new_lines
with open('<doc-path>', 'w', encoding='utf-8') as f:
    f.writelines(lines)
print(f'Replaced lines {start+1}-{end+1}')
PYEOF
```

**Cross-reference check after renames:**

When a comment renames a field/class/enumeration, grep for ALL occurrences:

```bash
grep -n '<old_name>' <doc-path>
```

### 4. Rebuild playground

After applying changes:
1. Re-read the updated document
2. **Delete any existing review HTML in the doc directory** — stale files cause bugs
3. Write updated JSON and re-run the build script with `--serve`

### 5. Explicit confirmation check

Ask the user to explicitly choose:

```
本次 review 完成了吗？
- 如果还需要修改 → 告诉我具体内容，我会继续
- 如果已完成 → 说"确认完成"，我会删除临时文件并结束
```

**Only these phrases trigger cleanup and exit:**
- "确认完成"、"可以了"、"没问题"、"完成了"

**Everything else is "continue"** — rebuild and loop (Step 4).

Repeat steps 2-4 until user explicitly confirms completion.

## When NOT to use this skill

- Simple typo fixes or one-line changes (just edit directly)
- Documents the user is still actively drafting (review comes after drafting)
- Non-text artifacts (images, binary files)
