#!/usr/bin/env node
/* eslint-disable @typescript-eslint/no-require-imports */
const fs = require('fs');
const path = require('path');

const swPath = path.resolve(__dirname, '..', 'public', 'sw.js');

if (!fs.existsSync(swPath)) {
  console.warn('normalize-sw: sw.js not found at', swPath);
  process.exit(0);
}

let content = fs.readFileSync(swPath, 'utf8');
let changed = false;

content = content.replace(/(["'])url\1\s*:\s*\1([^"']*)\1/g, (m, quote, url) => {
  if (!url.includes('\\')) return m;
  if (!/^[\\\/.]/.test(url)) return m;
  const normalized = url.replace(/\\/g, '/');
  changed = true;
  return m.replace(url, normalized);
});

if (changed) {
  fs.writeFileSync(swPath, content, 'utf8');
  console.log('normalize-sw: fixed URLs in', swPath);
} else {
  console.log('normalize-sw: no changes required');
}
