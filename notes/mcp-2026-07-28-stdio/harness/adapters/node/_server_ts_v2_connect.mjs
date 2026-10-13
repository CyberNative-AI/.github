// mcp-stdio-cross-era server adapter S for @modelcontextprotocol/server 2.x, hand-wired variant (impl ts-v2-<ver>-connect).
// Path: new McpServer(...) + server.connect(new StdioServerTransport()) -- the McpServer_connect_stdio /
// StdioServerTransport_basicUsage examples in server/dist/createMcpHandler-*.d.mts and stdio.d.mts.
// Run via the pinned entry files (server-*/client-*.mjs) or with NODE_MODULES_DIR=/envs/node/<prefix>/node_modules.
import './_prefix.mjs';

const { McpServer } = await import('@modelcontextprotocol/server');
const { StdioServerTransport } = await import('@modelcontextprotocol/server/stdio');
const z = await import('zod');

const server = new McpServer({ name: 'echo-server', version: '1.0.0' });
server.registerTool(
    'echo',
    { description: 'Echo the message', inputSchema: z.object({ message: z.string() }) },
    async ({ message }) => ({ content: [{ type: 'text', text: `echo:${message}` }] })
);
await server.connect(new StdioServerTransport());
