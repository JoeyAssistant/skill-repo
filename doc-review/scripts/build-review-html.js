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
  console.error('    "docLines": ["line1", "line2", ...]');
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

const { docPath, docLines, round = 1 } = input;

if (!docPath || !Array.isArray(docLines)) {
  console.error('Input must have docPath (string) and docLines (array)');
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

// Read JS libraries for inlining
function readLib(name, filename) {
  const libPath = path.join(scriptDir, '..', 'references', filename);
  try {
    const content = fs.readFileSync(libPath, 'utf8');
    console.log(name + ': loaded (' + Math.round(content.length / 1024) + ' KB)');
    return content;
  } catch (e) {
    console.warn('Warning: ' + filename + ' not found at', libPath);
    return '';
  }
}

const markedJs = readLib('marked.js', 'marked.min.js');
const highlightJs = readLib('highlight.js', 'highlight.min.js');
const mermaidJs = readLib('mermaid.js', 'mermaid.min.js');

// Escape for JS single-quoted string
function escJs(str) {
  return String(str).replace(/\\/g, '\\\\').replace(/'/g, "\\'").replace(/\n/g, '\\n').replace(/\r/g, '\\r');
}

// Build DOC_LINES JS array
const docLinesJs = docLines.map(function(l) { return "  '" + escJs(l) + "'"; }).join(',\n');

// Mermaid init
const mermaidInit = mermaidJs
  ? "mermaid.initialize({startOnLoad:false,theme:'default',securityLevel:'loose'});"
  : '/* mermaid not available */';

// Replace placeholders
const html = template
  .replace(/\/\* FILL: MARKED_JS \*\//, function() { return markedJs || '/* marked not loaded */'; })
  .replace(/\/\* FILL: HIGHLIGHT_JS \*\//, function() { return highlightJs || '/* highlight not loaded */'; })
  .replace(/\/\* FILL: MERMAID_JS \*\//, function() { return mermaidJs || '/* mermaid not loaded */'; })
  .replace(/\/\* FILL: MERMAID_INIT \*\//, function() { return mermaidInit; })
  .replace(/<!-- FILL: doc filename -->/g, function() { return path.basename(docPath); })
  .replace(/<!-- FILL: round number -->/g, function() { return String(round); })
  .replace(/<!-- FILL: doc path -->/g, function() { return escJs(docPath); })
  .replace(/<!-- FILL: doc filepath -->/g, function() { return escJs(docPath); })
  .replace(/\/\* FILL: DOC_LINES \*\//, function() { return docLinesJs; });

// Validate JS syntax
try {
  const scriptMatches = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)];
  for (const match of scriptMatches) {
    const code = match[1];
    if (code.length > 200000 || code.trim().length < 50) continue;
    new Function(code);
  }
  console.log('JS syntax validation: OK');
} catch (e) {
  console.error('JS syntax error in generated HTML:', e.message);
}

// Write output
fs.writeFileSync(outputPath, html, 'utf8');

// Line count verification
const htmlLinesMatch = html.match(/const DOC_LINES = \[([\s\S]*?)\];/);
if (htmlLinesMatch) {
  const htmlLineCount = htmlLinesMatch[1].split("',\n").length;
  if (htmlLineCount !== docLines.length) {
    console.warn('WARNING: line count mismatch. Source: ' + docLines.length + ', HTML: ' + htmlLineCount);
  } else {
    console.log('Line count verification: OK (' + docLines.length + ' lines)');
  }
}

console.log('Generated: ' + outputPath);
console.log('Document: ' + docPath + ' (' + docLines.length + ' lines, round ' + round + ')');

// Serve or open
if (serveMode) {
  const filename = path.basename(outputPath);
  const dir = path.dirname(outputPath);

  if (process.platform === 'darwin') {
    try { execSync('open "' + outputPath + '"', { stdio: 'inherit' }); console.log('Opened in browser (macOS)'); }
    catch (e) { console.error('Failed to open browser:', e.message); }
  } else if (process.env.DISPLAY && hasCommand('xdg-open')) {
    try { execSync('xdg-open "' + outputPath + '"', { stdio: 'inherit' }); console.log('Opened in browser (Linux GUI)'); }
    catch (e) { console.error('Failed to open browser:', e.message); }
  } else {
    serveWithPython(dir, filename);
  }
}

function hasCommand(cmd) {
  try { execSync('which ' + cmd + ' 2>/dev/null', { encoding: 'utf8' }); return true; }
  catch { return false; }
}

function serveWithPython(dir, filename) {
  const port = findAvailablePort(8123, 8999);
  const interfaces = os.networkInterfaces();
  const ips = [];
  for (const name of Object.keys(interfaces)) {
    for (const iface of interfaces[name]) {
      if (iface.family === 'IPv4' && !iface.internal) ips.push(iface.address);
    }
  }
  const pythonCmd = hasCommand('python3') ? 'python3' : (hasCommand('python') ? 'python' : null);
  if (!pythonCmd) { console.error('No Python found. Cannot start HTTP server.'); console.log('File is at: ' + path.join(dir, filename)); return; }
  const server = spawn(pythonCmd, ['-m', 'http.server', String(port)], { cwd: dir, stdio: ['pipe', 'pipe', 'pipe'], detached: false });
  console.log('\n=== HTTP Server Started (headless Linux) ===');
  console.log('Open in your browser:');
  console.log('  http://localhost:' + port + '/' + filename);
  for (const ip of ips) console.log('  http://' + ip + ':' + port + '/' + filename);
  console.log('Press Ctrl+C to stop the server.\n');
  server.stdout.on('data', function(data) { var msg = data.toString().trim(); if (msg) console.log('[http]', msg); });
  server.stderr.on('data', function(data) { var msg = data.toString().trim(); if (msg && !msg.includes('Serving HTTP')) console.log('[http]', msg); });
  process.on('SIGINT', function() { server.kill(); process.exit(0); });
  process.on('SIGTERM', function() { server.kill(); process.exit(0); });
  server.on('close', function() { process.exit(0); });
}

function findAvailablePort(start, end) {
  for (var p = start; p <= end; p++) {
    try { var s = require('net').createServer(); s.listen(p); s.close(); return p; } catch {}
  }
  return 8080;
}
