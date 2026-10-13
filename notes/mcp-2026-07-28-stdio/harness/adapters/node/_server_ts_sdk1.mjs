// mcp-stdio-cross-era server adapter S for @modelcontextprotocol/sdk 1.x (impl ts-sdk-<ver>; used for 1.29.0 and 1.32.1).
// Documented default path: McpServer + registerTool + StdioServerTransport (sdk README / mcp.d.ts examples).
// Run via the pinned entry files (server-*/client-*.mjs) or with NODE_MODULES_DIR=/envs/node/<prefix>/node_modules.
import './_prefix.mjs';

const { McpServer } = await import('@modelcontextprotocol/sdk/server/mcp.js');
const { StdioServerTransport } = await import('@modelcontextprotocol/sdk/server/stdio.js');
const z = await import('zod/v4');

const server = new McpServer({ name: 'echo-server', version: '1.0.0' });
server.registerTool(
    'echo',
    { description: 'Echo the message', inputSchema: { message: z.string() } },
    async ({ message }) => ({ content: [{ type: 'text', text: `echo:${message}` }] })
);
await server.connect(new StdioServerTransport());
