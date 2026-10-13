// mcp-stdio-cross-era server adapter S for @modelcontextprotocol/server 2.x (impl ts-v2-<ver>).
// Path: serveStdio(factory) from '@modelcontextprotocol/server/stdio' with no options -- the v2 stdio
// serving entry documented in server/dist/stdio.d.mts ("the same factory serves both eras").
// See server_ts_v2_connect.mjs for the hand-wired McpServer.connect(new StdioServerTransport()) variant.
// Run via the pinned entry files (server-*/client-*.mjs) or with NODE_MODULES_DIR=/envs/node/<prefix>/node_modules.
import './_prefix.mjs';

const { McpServer } = await import('@modelcontextprotocol/server');
const { serveStdio } = await import('@modelcontextprotocol/server/stdio');
const z = await import('zod');

serveStdio(() => {
    const server = new McpServer({ name: 'echo-server', version: '1.0.0' });
    server.registerTool(
        'echo',
        { description: 'Echo the message', inputSchema: z.object({ message: z.string() }) },
        async ({ message }) => ({ content: [{ type: 'text', text: `echo:${message}` }] })
    );
    return server;
});
