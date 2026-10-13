// mcp-stdio-cross-era client adapter C for @modelcontextprotocol/client 2.x (impl ts-v2-<ver>).
// Default path: new Client({name, version}) + new StdioClientTransport({command, args}) from
// '@modelcontextprotocol/client/stdio' + connect() (Client_connect_stdio example). No versionNegotiation option.
// Run via the pinned entry files (server-*/client-*.mjs) or with NODE_MODULES_DIR=/envs/node/<prefix>/node_modules.
import { pkgVersion } from './_prefix.mjs';
import { runClient, fmtInfo } from './_client_common.mjs';

const { Client } = await import('@modelcontextprotocol/client');
const { StdioClientTransport } = await import('@modelcontextprotocol/client/stdio');

await runClient({
    impl: `ts-v2-${pkgVersion('@modelcontextprotocol/client')}`,
    Client,
    StdioClientTransport,
    negotiated: (c) => {
        const v = c.getNegotiatedProtocolVersion?.();
        const era = c.getProtocolEra?.();
        return v ? (era ? `${v} (${era})` : v) : (era ?? null);
    },
    serverInfo: (c) => fmtInfo(c.getServerVersion())
});
