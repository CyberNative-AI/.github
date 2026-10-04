// Copyright (c) 2026 CyberNative AI LLC. MIT licensed; see LICENSE.
import assert from 'node:assert/strict';
import { mkdtempSync, writeFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { spawnSync } from 'node:child_process';

// All inputs are authored toy fixtures. No downloads or packages are required.
const directory = mkdtempSync(join(tmpdir(), 'native-ts-example-'));
try {
  const files = {
    'package.json': JSON.stringify({
      type: 'module',
      imports: { '#invoice/total': './total.ts' },
    }),
    'tsconfig.json': JSON.stringify({
      compilerOptions: {
        strict: true,
        paths: { '@invoice/total': ['./total.ts'] },
      },
    }),
    'total.ts': 'export const cents: number = 700;\n',
    'annotation.ts':
      "const amount: number = 'seven';\nconsole.log(typeof amount, amount);\n",
    'paths.ts':
      "import { cents } from '@invoice/total';\nconsole.log(cents);\n",
    'imports.ts':
      "import { cents } from '#invoice/total';\nconsole.log(cents);\n",
  };
  for (const [name, source] of Object.entries(files)) {
    writeFileSync(join(directory, name), source);
  }

  const run = (file) => {
    const result = spawnSync(process.execPath, [file], {
      cwd: directory,
      // Exclude inherited loaders and NODE_OPTIONS from this controlled example.
      env: {},
      encoding: 'utf8',
      timeout: 5000,
      maxBuffer: 16384,
    });
    if (result.error) throw result.error;
    assert.equal(result.signal, null, `${file}: terminated by a signal`);
    return result;
  };

  console.log(`Node ${process.version}`);
  const annotation = run('annotation.ts');
  assert.equal(annotation.status, 0, annotation.stderr);
  assert.equal(annotation.stdout, 'string seven\n');
  console.log('Mismatched annotation: string seven (exit 0)');

  const paths = run('paths.ts');
  assert.equal(paths.status, 1);
  assert.equal(paths.stdout, '');
  assert.match(paths.stderr, /ERR_MODULE_NOT_FOUND/);
  console.log('tsconfig-only @ alias: ERR_MODULE_NOT_FOUND (exit 1)');

  const imports = run('imports.ts');
  assert.equal(imports.status, 0, imports.stderr);
  assert.equal(imports.stdout, '700\n');
  console.log('package.json # import: 700 (exit 0)');
} finally {
  rmSync(directory, { recursive: true, force: true });
}
