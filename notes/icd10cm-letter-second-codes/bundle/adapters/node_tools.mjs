// npm adapters. Usage: node node_tools.mjs PROBES OUTDIR NODE_MODULES ORDERFILE [tool...]
import fs from "node:fs"; import path from "node:path"; import { createRequire } from "node:module";
const [probesPath, outDir, nm, orderFile, ...only] = process.argv.slice(2);
const probes = fs.readFileSync(probesPath, "utf8").trim().split("\n").map(JSON.parse);
fs.mkdirSync(outDir, { recursive: true });
const imp = (p) => import(path.join(nm, p));
const TOOLS = {
  "@lowlysre/icd-10-cm": async () => { const m = await imp("@lowlysre/icd-10-cm/dist/index.mjs").catch(() => createRequire(nm + "/")("@lowlysre/icd-10-cm"));
    const g = m.getICD10Description ?? m.default; return ["@lowlysre/icd-10-cm 3.1.1 getICD10Description(dotted) " + JSON.stringify(m.ICD10_CM_RELEASE ?? null),
    (p) => { const r = g(p.dotted); return [r !== undefined && r !== null, r]; }]; },
  "icdwise": async () => { const m = await imp("icdwise/dist/index.js");
    return ["icdwise 0.1.2 validateIcd10(dotted).valid dataset=" + m.datasetVersion, (p) => { const r = m.validateIcd10(p.dotted); return [r.valid === true, r]; }]; },
  "@cyanheads/medical-codes-mcp-server": async () => { const m = await imp("@cyanheads/medical-codes-mcp-server/dist/services/code-index/code-index-service.js");
    await m.initCodeIndexService(); const s = m.getCodeIndexService();
    return ["@cyanheads/medical-codes-mcp-server 0.4.1 checkCode(dotted) [system auto, as medcode check_code without system]",
      (p) => { const r = s.checkCode(p.dotted); const st = r.kind === "resolved" ? r.result.status : r.kind; return [String(st).startsWith("valid"), st + " " + (r.result?.whyNot ?? "")]; }]; },
  "@easysolutions906/mcp-healthcare": async () => { const m = await imp("@easysolutions906/mcp-healthcare/src/tools/icd10.js");
    return ["@easysolutions906/mcp-healthcare 1.1.3 validate(dotted).valid", (p) => { const r = m.validate(p.dotted); return [r.valid === true, r.message ?? r.description]; }]; },
  "@cosyte/terminology": async () => { const m = await imp("@cosyte/terminology/dist/index.mjs");
    const cs = m.loadCodeSystem({ format: "fixed-width", content: fs.readFileSync(orderFile, "latin1"), fields: m.ICD10CM_ORDER_FILE_FIELDS });
    return ["@cosyte/terminology 0.1.0 loadCodeSystem(fixed-width FY2027 order file, ICD10CM_ORDER_FILE_FIELDS) + validateCode(undotted); count=" + cs.count,
      (p) => { const r = m.validateCode(cs, p.code); return [r.valid === true, JSON.stringify(r).slice(0, 150)]; }]; },
};
for (const name of (only.length ? only : Object.keys(TOOLS))) {
  const file = path.join(outDir, name.replace(/[@/]/g, "_") + ".jsonl"); let call, fn;
  try { [call, fn] = await TOOLS[name](); } catch (e) { fs.writeFileSync(file, JSON.stringify({ tool: name, setup_error: String(e?.stack ?? e).slice(0, 800) }) + "\n"); console.log(name, "SETUP ERROR"); continue; }
  const rows = probes.map((p) => { try { const [ok, raw] = fn(p); return { tool: name, call, arm: p.arm, code: p.code, accept: !!ok, raw: raw === undefined || raw === null ? null : (typeof raw === "string" ? raw : JSON.stringify(raw)).slice(0, 160), error: null }; }
    catch (e) { return { tool: name, call, arm: p.arm, code: p.code, accept: false, raw: null, error: String(e).slice(0, 200) }; } });
  fs.writeFileSync(file, rows.map((r) => JSON.stringify(r, Object.keys(r).sort())).join("\n") + "\n");
  console.log(name, rows.filter((r) => r.accept).length, "/", rows.length);
}
process.exit(0);
