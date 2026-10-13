// Resolve otp-version specs with setup-beam's own matching code: the functions below are
// extracted verbatim from src/setup-beam.js of an erlef/setup-beam checkout and run with the
// checkout's semver (npm ci --ignore-scripts). One JSON line per spec, as checkbeam2604.py.
// usage: node oracle.mjs SETUP_BEAM_DIR BUILDS_24.04 BUILDS_26.04 < specs.jsonl
import fs from 'node:fs'
import path from 'node:path'
import { createRequire } from 'node:module'
const [dir, b24, b26] = process.argv.slice(2)
const semver = createRequire(path.join(path.resolve(dir), 'package.json'))('semver')
const code = fs.readFileSync(path.join(dir, 'src', 'setup-beam.js'), 'utf8')
const want = ['maybeRemoveOTPPrefix', 'getVersionFromSpec', 'maybeCoerced', 'sortVersions', 'isRC',
  'isKnownBranch', 'isKnownVerBranch', 'gt', 'validVersion', 'parseVersion', 'maybeRemoveVPrefix',
  'xyzAbcVersion', 'versionAbc', 'isVersion']
function extract(name) {
  const start = code.indexOf(`\nfunction ${name}(`)
  if (start < 0) throw new Error(`missing ${name}`)
  return code.slice(start, code.indexOf('\n}\n', start) + 3)
}
const consts = ['knownBranches', 'nonSpecificVersions'].map((n) => code.match(new RegExp(`\\nconst ${n} = .*`))[0]).join('\n')
let STRICT = false
const fns = new Function('semver', 'core', 'isStrictVersion',
  `${consts}\n${want.map(extract).join('\n')}\nreturn { getVersionFromSpec, maybeRemoveOTPPrefix }`)(
  semver, { debug() {} }, () => STRICT)
function listing(file) { // getOTPVersions, linux branch
  const v = {}
  fs.readFileSync(file, 'utf8').trim().split('\n').forEach((line) => {
    const orig = line.match(/^([^ ]+)?( .+)/)[1]
    v[fns.maybeRemoveOTPPrefix(orig)] = orig
  })
  return v
}
const L = { '24.04': listing(b24), '26.04': listing(b26) }
function resolve(spec, os) { // getOTPVersion
  try {
    return fns.getVersionFromSpec(fns.maybeRemoveOTPPrefix(spec), { ...L[os] })
  } catch (e) {
    return `ERROR ${e.message}`
  }
}
for (const line of fs.readFileSync(0, 'utf8').split('\n').filter(Boolean)) {
  const { spec, strict } = JSON.parse(line)
  STRICT = !!strict
  console.log(JSON.stringify({ spec, strict: !!strict, '24.04': resolve(spec, '24.04'), '26.04': resolve(spec, '26.04') }))
}
