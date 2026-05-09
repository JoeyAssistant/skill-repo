#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');
const { execSync, spawn } = require('child_process');
const os = require('os');
const http = require('http');

const args = process.argv.slice(2);
const serveMode = args.includes('--serve');
if (serveMode) args.splice(args.indexOf('--serve'), 1);

if (args.length < 1) {
  console.error('Usage: node build-review-html.js [--serve] <input.json> [output.html]');
  console.error('');
  console.error('Options:');
  console.error('  --serve    Auto-detect environment and open/serve the HTML');
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

// Read mermaid.min.js for inlining
const mermaidPath = path.join(scriptDir, '..', 'references', 'mermaid.min.js');
let mermaidJs = '';
try {
  mermaidJs = fs.readFileSync(mermaidPath, 'utf8');
  console.log('Mermaid JS: loaded (' + Math.round(mermaidJs.length / 1024) + ' KB)');
} catch (e) {
  console.warn('Warning: mermaid.min.js not found at', mermaidPath, '- mermaid diagrams will not render');
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

// Mermaid init code
const mermaidInit = mermaidJs
  ? `mermaid.initialize({startOnLoad:false,theme:'dark',securityLevel:'loose'});`
  : '/* mermaid not available */';

// Replace placeholders in template
// Use function replacers to avoid $&/$`/$' special pattern interpretation
const html = template
  .replace(/\/\* FILL: MERMAID_JS \*\//, () => mermaidJs || '/* mermaid not loaded */')
  .replace(/\/\* FILL: MERMAID_INIT \*\//, () => mermaidInit)
  .replace(/<!-- FILL: doc filename -->/g, () => path.basename(docPath))
  .replace(/<!-- FILL: round number -->/g, () => String(round))
  .replace(/<!-- FILL: doc path -->/g, () => escJs(docPath))
  .replace(/<!-- FILL: doc filepath -->/g, () => escJs(docPath))
  .replace(/\/\* FILL: DOC_LINES \*\//, () => docLinesJs)
  .replace(/\/\* FILL: autoSuggestions \*\//, () => suggestionsJs);

// Validate JS syntax (skip mermaid block — known-good library code)
try {
  const scriptMatches = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)];
  for (const match of scriptMatches) {
    const code = match[1];
    // Skip large blocks (mermaid.min.js) and empty/template blocks
    if (code.length > 200000 || code.trim().startsWith('/*') || code.trim().length < 50) continue;
    new Function(code);
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

// Serve or open the file
if (serveMode) {
  const filename = path.basename(outputPath);
  const dir = path.dirname(outputPath);

  if (process.platform === 'darwin') {
    try {
      execSync(`open "${outputPath}"`, { stdio: 'inherit' });
      console.log('Opened in browser (macOS)');
    } catch (e) {
      console.error('Failed to open browser:', e.message);
    }
  } else if (process.env.DISPLAY && hasCommand('xdg-open')) {
    try {
      execSync(`xdg-open "${outputPath}"`, { stdio: 'inherit' });
      console.log('Opened in browser (Linux GUI)');
    } catch (e) {
      console.error('Failed to open browser:', e.message);
    }
  } else {
    serveWithPython(dir, filename);
  }
}

function hasCommand(cmd) {
  try { execSync(`which ${cmd} 2>/dev/null`, { encoding: 'utf8' }); return true; }
  catch { return false; }
}

function serveWithPython(dir, filename) {
  const port = findAvailablePort(8123, 8999);
  const hostname = os.hostname();
  const interfaces = os.networkInterfaces();
  const ips = [];
  for (const name of Object.keys(interfaces)) {
    for (const iface of interfaces[name]) {
      if (iface.family === 'IPv4' && !iface.internal) {
        ips.push(iface.address);
      }
    }
  }

  const hasPython3 = hasCommand('python3');
  const pythonCmd = hasPython3 ? 'python3' : (hasCommand('python') ? 'python' : null);

  if (!pythonCmd) {
    console.error('No Python found. Cannot start HTTP server.');
    console.log(`File is at: ${path.join(dir, filename)}`);
    console.log('Please copy it to a machine with a browser.');
    return;
  }

  const server = spawn(pythonCmd, ['-m', 'http.server', String(port)], {
    cwd: dir,
    stdio: ['pipe', 'pipe', 'pipe'],
    detached: false
  });

  console.log('\n=== HTTP Server Started (headless Linux) ===');
  console.log(`Open in your browser:`);
  console.log(`  http://localhost:${port}/${filename}`);
  for (const ip of ips) {
    console.log(`  http://${ip}:${port}/${filename}`);
  }
  console.log('Press Ctrl+C to stop the server.\n');

  server.stdout.on('data', (data) => {
    const msg = data.toString().trim();
    if (msg) console.log('[http]', msg);
  });
  server.stderr.on('data', (data) => {
    const msg = data.toString().trim();
    if (msg && !msg.includes('Serving HTTP')) console.log('[http]', msg);
  });

  process.on('SIGINT', () => {
    server.kill();
    process.exit(0);
  });
  process.on('SIGTERM', () => {
    server.kill();
    process.exit(0);
  });

  // Keep the process alive
  server.on('close', () => process.exit(0));
}

function findAvailablePort(start, end) {
  for (let port = start; port <= end; port++) {
    try {
      const s = require('net').createServer();
      s.listen(port);
      s.close();
      return port;
    } catch {}
  }
  return 8080;
}
