'use strict';
const fs = require('node:fs');
const path = require('node:path');
const {createRequire} = require('node:module');
const supported = ['cron', 'node-cron', 'node-schedule'];
function projectRequire(projectDir) {
  return createRequire(path.join(projectDir, '__dst_check_project__.cjs'));
}
function packageInfo(name, projectDir) {
  if (!supported.includes(name)) throw new Error('Supported libraries in this partial build: ' + supported.join(', '));
  const req = projectRequire(projectDir);
  let entry;
  try { entry = req.resolve(name); }
  catch (_) { throw new Error('Could not resolve ' + name + ' from the selected project node_modules. Run dst-check from the project or pass --project.'); }
  let dir = path.dirname(entry);
  while (true) {
    const file = path.join(dir, 'package.json');
    if (fs.existsSync(file)) {
      try {
        const meta = JSON.parse(fs.readFileSync(file, 'utf8'));
        if (meta.name === name && typeof meta.version === 'string') return {name, version: meta.version, entry, directory: dir};
      } catch (_) {}
    }
    const parent = path.dirname(dir);
    if (parent === dir) break;
    dir = parent;
  }
  throw new Error('Could not find package metadata for resolved ' + name + ' entry: ' + entry);
}
module.exports = {supported, projectRequire, packageInfo};
