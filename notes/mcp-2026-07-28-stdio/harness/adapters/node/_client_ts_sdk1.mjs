// mcp-stdio-cross-era client adapter C for @modelcontextprotocol/sdk 1.x (impl ts-sdk-<ver>; used for 1.29.0 and 1.32.1).
// Default path: new Client({name, version}) + new StdioClientTransport({command, args}) + connect().
// Run via the pinned entry files (server-*/client-*.mjs) or with NODE_MODULES_DIR=/envs/node/<prefix>/node_modules.
import { pkgVersion } from './_prefix.mjs';
import { runClient, fmtInfo } from './_client_common.mjs';

const { Client } = await import('@modelcontextprotocol/sdk/client/index.js');
const { StdioClientTransport } = await import('@modelcontextprotocol/sdk/client/stdio.js');

await runClient({
    impl: `ts-sdk-${pkgVersion('@modelcontextprotocol/sdk')}`,
    Client,
    StdioClientTransport,
    // 1.x Client does not expose the negotiated protocol version (no getter in client/index.js).
    negotiated: (c) => (typeof c.getNegotiatedProtocolVersion === 'function' ? c.getNegotiatedProtocolVersion() : null),
    serverInfo: (c) => fmtInfo(c.getServerVersion())
});
