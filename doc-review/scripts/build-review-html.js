#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');

const args = process.argv.slice(2);
if (args.length < 1) {
  console.error('Usage: node build-review-html.js <input.json> [output.html]');
  console.error('');
  console.error('Input JSON format:');
  console.error('  {');
  console.error('    "docPath": "path/to/doc.md",');
  console.error('    "round": 1,');
  console.error('    "docLines": ["line1", "line2", ...],');
  console.error('    "suggestions": [{');
  console.error('      "id": "a1",');
  console.error('      "lineRef": "Line 5-27",');
  console.error('      "targetLineStart": 5,');
  console.error('      "targetLineEnd": 27,');
  console.error('      "targetText": "short excerpt",');
  console.error('      "suggestion": "what to improve",');
  console.error('      "category": "clarity"');
  console.error('    }]');
  console.error('  }');
  process.exit(1);
}

const inputPath = path.resolve(args[0]);
const outputPath = args[1] ? path.resolve(args[1]) : inputPath.replace(/\.json$/, '.html');
const scriptDir = __dirname;

// Read and parse input
let input;
try {
  input = JSON.parse(fs.readFileSync(inputPath, 'utf8'));
} catch (e) {
  console.error('Failed to read/parse input JSON:', e.message);
  process.exit(1);
}

const { docPath, docLines, suggestions = [], round = 1 } = input;

if (!docPath || !Array.isArray(docLines)) {
  console.error('Input must have docPath (string) and docLines (array)');
  process.exit(1);
}

// Validate suggestion targetText matches actual line content
let hasTargetMismatch = false;
for (const s of suggestions) {
  const lineIdx = (s.targetLineStart || 1) - 1;
  const actualLine = docLines[lineIdx] || '';
  const targetText = s.targetText || '';
  // Check if targetText is a substring of the actual line (handles escaping differences)
  const normalizedLine = actualLine.replace(/\\n/g, '\n').replace(/\\r/g, '\r').replace(/\\\\/g, '\\').replace(/\\'/g, "'");
  if (targetText && !normalizedLine.includes(targetText)) {
    console.error(`ERROR: suggestion '${s.id}' targetText mismatch`);
    console.error(`  lineRef: ${s.lineRef}`);
    console.error(`  targetLineStart: ${s.targetLineStart}`);
    console.error(`  expected (first 60 chars): "${actualLine.slice(0, 60)}"`);
    console.error(`  targetText (first 60 chars): "${targetText.slice(0, 60)}"`);
    hasTargetMismatch = true;
  }
}
if (hasTargetMismatch) {
  console.error('Target text mismatch errors detected. Fix the JSON before rebuilding.');
  process.exit(1);
}

// Read the HTML template
const templatePath = path.join(scriptDir, '..', 'references', 'review-template.html');
let template;
try {
  template = fs.readFileSync(templatePath, 'utf8');
} catch (e) {
  console.error('Failed to read template:', templatePath, e.message);
  process.exit(1);
}

// Escape a string for use inside a JS single-quoted string
function escJs(str) {
  return String(str)
    .replace(/\\/g, '\\\\')
    .replace(/'/g, "\\'")
    .replace(/\n/g, '\\n')
    .replace(/\r/g, '\\r');
}

// Build DOC_LINES JS array
const docLinesJs = docLines.map(l => `  '${escJs(l)}'`).join(',\n');

// Build suggestions JS array
const suggestionsJs = suggestions.map((s, i) => {
  const id = s.id || `a${i + 1}`;
  const lineRef = s.lineRef || `Line ${s.targetLineStart}${s.targetLineEnd !== s.targetLineStart ? '-' + s.targetLineEnd : ''}`;
  return `  {
    id: '${escJs(id)}',
    lineRef: '${escJs(lineRef)}',
    targetLineStart: ${s.targetLineStart},
    targetLineEnd: ${s.targetLineEnd || s.targetLineStart},
    targetText: '${escJs(s.targetText || '')}',
    suggestion: '${escJs(s.suggestion || '')}',
    category: '${escJs(s.category || 'clarity')}',
    status: 'pending',
    userComment: '',
    source: 'auto'
  }`;
}).join(',\n');

// Replace placeholders in template
const html = template
  .replace(/<!-- FILL: doc filename -->/g, path.basename(docPath))
  .replace(/<!-- FILL: round number -->/g, String(round))
  .replace(/<!-- FILL: doc path -->/g, escJs(docPath))
  .replace(/<!-- FILL: doc filepath -->/g, escJs(docPath))
  .replace(/\/\* FILL: DOC_LINES \*\//, docLinesJs)
  .replace(/\/\* FILL: autoSuggestions \*\//, suggestionsJs);

// Validate JS syntax
try {
  const scriptMatch = html.match(/<script>([\s\S]*?)<\/script>/);
  if (scriptMatch) {
    new Function(scriptMatch[1]);
  }
  console.log('JS syntax validation: OK');
} catch (e) {
  console.error('JS syntax error in generated HTML:', e.message);
  console.error('Writing HTML for debugging...');
}

// Write output
fs.writeFileSync(outputPath, html, 'utf8');

// Verify DOC_LINES count
const actualLines = docLines.length;
const htmlLinesMatch = html.match(/const DOC_LINES = \[([\s\S]*?)\];/);
if (htmlLinesMatch) {
  const htmlLineCount = htmlLinesMatch[1].split("',\n").length;
  if (htmlLineCount !== actualLines) {
    console.warn(`WARNING: line count mismatch. Source: ${actualLines}, HTML: ${htmlLineCount}`);
  } else {
    console.log(`Line count verification: OK (${actualLines} lines)`);
  }
}

console.log(`Generated: ${outputPath}`);
console.log(`Document: ${docPath} (${actualLines} lines, ${suggestions.length} suggestions, round ${round})`);
