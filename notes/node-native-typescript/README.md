# Node's native TypeScript: two checks before dropping your runner

A `.ts` file that runs can still contain a wrong type annotation. On Node v24.21.0,
our deliberately mistyped number ran as the string `seven`. An import alias
defined only in `tsconfig.json` then failed to resolve.

If you're moving a small script to native Node execution, check its types and its
imports separately. A successful run answers neither question for every input.

## Reproduce without installing a package

Download [reproduce.mjs](./reproduce.mjs), then run:

```sh
node --version
node reproduce.mjs
```

The example creates and removes an isolated temporary directory, writes six toy
files, and runs three local Node processes. It makes no network requests and
reads no project files. Checked October 4, 2026, with Node v24.21.0:

```text
Node v24.21.0
Mismatched annotation: string seven (exit 0)
tsconfig-only @ alias: ERR_MODULE_NOT_FOUND (exit 1)
package.json # import: 700 (exit 0)
```

The first fixture is intentionally mistyped:

```ts
const amount: number = 'seven';
console.log(typeof amount, amount);
```

Running it strips the annotation; it does not check the assignment. Keep your
project's type-check command as a separate step. Node's [TypeScript documentation](https://nodejs.org/docs/latest-v24.x/api/typescript.html#type-stripping)
describes this boundary and the configuration for a separate compiler check.

## Give the runtime its own import mapping

The failed fixture imports `@invoice/total`. Its `tsconfig.json` maps that name
to `./total.ts`, but Node doesn't read that configuration. The successful fixture
imports `#invoice/total`, defined in its `package.json`:

```json
{
  "type": "module",
  "imports": {
    "#invoice/total": "./total.ts"
  }
}
```

```ts
import { cents } from '#invoice/total';
console.log(cents);
```

This is Node's [package subpath import](https://nodejs.org/docs/latest-v24.x/api/packages.html#subpath-imports),
which uses a `#` prefix. It is a runtime mapping for this small example. Check the
compiler side too when applying it to your project.

## Scope

These are three authored fixtures on one Node version, with inherited loaders
and `NODE_OPTIONS` excluded. No TypeScript compiler, third-party runner, other
Node version, dependency package, application migration or performance comparison
was tested. The linked 24.x documentation displayed v24.21.0 on the check date;
the live links can change as that release line advances.

Published by CyberNative AI LLC with AI assistance. Corrections:
hello@cybernative.ai. Original example and note: [MIT license](./LICENSE).
