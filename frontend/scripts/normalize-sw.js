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

content = content.replace(/('url'\\s*:\\s*')([^']*)(')/g, (m, p1, url, p3) => {
  if (!url.includes('\\\\')) return m;
  if (!/^[\\/_.]/.test(url)) return m;
  const normalized = url.replace(/\\\\/g, '/');
  changed = true;
  return `${p1}${normalized}${p3}`;
});

if (changed) {
  fs.writeFileSync(swPath, content, 'utf8');
  console.log('normalize-sw: fixed URLs in', swPath);
} else {
  console.log('normalize-sw: no changes required');
}
