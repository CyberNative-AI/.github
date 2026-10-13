// mcp-stdio-cross-era shared client-adapter driver (contract: CONTRACT.md "Client adapter C").
// Each SDK-specific adapter passes its Client / StdioClientTransport classes; this driver uses only the
// SDK defaults: new StdioClientTransport({command, args}), new Client({name, version}), connect(transport),
// listTools(), callTool({name, arguments}), close(). No version/mode/timeout/compat options are passed.
import { performance } from 'node:perf_hooks';

const DEADLINE_MS = 40_000; // harness guard only (outer harness kills at 45 s)

export function parseInvocation() {
    const argv = process.argv.slice(2);
    const i = argv.indexOf('--');
    const cmd = i >= 0 ? argv.slice(i + 1) : [];
    if (cmd.length === 0) {
        process.stderr.write('usage: node <client>.mjs -- SERVER_CMD [ARGS...]\n');
        process.exit(2);
    }
    const tool = process.env.MCP_TOOL || 'echo';
    const args = process.env.MCP_ARGS ? JSON.parse(process.env.MCP_ARGS) : { message: 'hello-re13340' };
    return { command: cmd[0], args: cmd.slice(1), tool, toolArgs: args };
}

export async function runClient({ impl, Client, StdioClientTransport, negotiated, serverInfo }) {
    const inv = parseInvocation();
    const out = {
        impl,
        connect_ok: false, list_ok: false, call_ok: false,
        tools: null, call_text: null, call_is_error: null,
        negotiated: null, server_info: null,
        t_connect_ms: null, t_list_ms: null, t_call_ms: null,
        error_stage: null, error_type: null, error_msg: null
    };
    let stage = 'connect';
    let printed = false;
    const emit = () => {
        if (printed) return;
        printed = true;
        process.stdout.write(JSON.stringify(out) + '\n', () => process.exit(0));
    };
    const fail = (err) => {
        if (out.error_stage !== null) return;
        out.error_stage = stage;
        out.error_type = err?.constructor?.name ?? typeof err;
        const code = err && typeof err === 'object' && 'code' in err ? ` [code=${err.code}]` : '';
        out.error_msg = (String(err?.message ?? err) + code).slice(0, 500);
    };

    const transport = new StdioClientTransport({ command: inv.command, args: inv.args });
    const client = new Client({ name: 're13340-client', version: '1.0.0' });

    const deadline = setTimeout(() => {
        fail(Object.assign(new Error(`internal deadline ${DEADLINE_MS} ms exceeded during ${stage}`), { name: 'InternalDeadline' }));
        out.error_type = 'InternalDeadline';
        transport.close().catch(() => {}).finally(emit);
        setTimeout(emit, 2000).unref();
    }, DEADLINE_MS);

    const t0 = performance.now();
    const ms = () => Math.round((performance.now() - t0) * 10) / 10;
    try {
        await client.connect(transport);
        out.connect_ok = true;
        out.t_connect_ms = ms();
        out.negotiated = negotiated(client) ?? null;
        out.server_info = serverInfo(client) ?? null;

        stage = 'list';
        const listed = await client.listTools();
        out.list_ok = true;
        out.t_list_ms = ms();
        out.tools = (listed.tools ?? []).map((t) => t.name).sort();

        stage = 'call';
        const res = await client.callTool({ name: inv.tool, arguments: inv.toolArgs });
        out.call_ok = true;
        out.t_call_ms = ms();
        out.call_text = (res.content ?? []).filter((c) => c.type === 'text').map((c) => c.text).join('');
        out.call_is_error = res.isError === true;

        stage = 'close';
        await client.close();
    } catch (err) {
        fail(err);
        try { await client.close(); } catch { /* best effort */ }
        try { await transport.close(); } catch { /* best effort */ }
    }
    clearTimeout(deadline);
    emit();
}

/** "name/version" string from an Implementation object, or null. */
export const fmtInfo = (v) => (v && typeof v === 'object' ? `${v.name}/${v.version}` : null);
