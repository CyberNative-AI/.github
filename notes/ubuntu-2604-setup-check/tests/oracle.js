// node-semver oracle: prints satisfies(v, r) for every pair, "ERR" when the range is invalid
const semver = require('/usr/local/lib/node_modules/npm/node_modules/semver');
const c = JSON.parse(require('fs').readFileSync('/t/semver-cases.json'));
const out = {};
for (const r of c.ranges) {
  if (semver.validRange(r) === null) { out[r] = 'ERR'; continue; }
  out[r] = c.versions.filter(v => semver.satisfies(v, r));
}
console.log(JSON.stringify(out));
