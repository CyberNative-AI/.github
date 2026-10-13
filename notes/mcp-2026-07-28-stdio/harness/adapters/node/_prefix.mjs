// mcp-stdio-cross-era module-resolution shim for the Node adapters (no build step, no copied packages).
//
// ESM ignores NODE_PATH. The harness sets NODE_MODULES_DIR=/envs/node/<prefix>/node_modules and runs
// `node /src/adapters/node/<adapter>.mjs`. This module installs a resolve hook that resolves every
// bare specifier as if the importing file lived at /envs/node/<prefix>/ (Node's own ESM resolver with
// the "import" condition; transitive imports inside the packages resolve natively). Adapters import
// this file statically and then load the SDK with dynamic import(), so the hook is active first.
// Diagnostics go to stderr only; stdout is reserved for protocol traffic / the result line.
import * as nodeModule from 'node:module';
import { readFileSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { pathToFileURL } from 'node:url';

const dir = process.env.NODE_MODULES_DIR;
if (!dir) {
    process.stderr.write('re13340 adapter: NODE_MODULES_DIR is required (e.g. /envs/node/ts-sdk-1.29.0/node_modules)\n');
    process.exit(2);
}
export const NODE_MODULES_DIR = resolve(dir);
const PARENT_URL = pathToFileURL(join(NODE_MODULES_DIR, '..', '__re13340_parent__.mjs')).href;

const isBare = (s) => !(s.startsWith('.') || s.startsWith('/') || s.includes(':'));

if (typeof nodeModule.registerHooks === 'function') {
    nodeModule.registerHooks({
        resolve(specifier, context, nextResolve) {
            if (isBare(specifier) && context.parentURL && context.parentURL.startsWith(pathToFileURL(import.meta.dirname).href)) {
                return nextResolve(specifier, { ...context, parentURL: PARENT_URL });
            }
            return nextResolve(specifier, context);
        }
    });
} else {
    const src = `const P=${JSON.stringify(PARENT_URL)},D=${JSON.stringify(pathToFileURL(import.meta.dirname).href)};
export async function resolve(s,c,n){if(!(s.startsWith('.')||s.startsWith('/')||s.includes(':'))&&c.parentURL&&c.parentURL.startsWith(D))return n(s,{...c,parentURL:P});return n(s,c);}`;
    nodeModule.register('data:text/javascript,' + encodeURIComponent(src));
}

/** Installed version of a package in the selected prefix (read from its package.json). */
export function pkgVersion(name) {
    return JSON.parse(readFileSync(join(NODE_MODULES_DIR, name, 'package.json'), 'utf8')).version;
}
