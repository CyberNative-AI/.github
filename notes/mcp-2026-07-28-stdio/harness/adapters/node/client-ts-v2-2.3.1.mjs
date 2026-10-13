// mcp-stdio-cross-era entry point: pins the npm prefix /envs/node/ts-v2-2.3.1 and runs _client_ts_v2.mjs.
// The prefix is baked in (not read from the environment) because SDK stdio client transports spawn
// servers with a filtered default environment, and an inherited NODE_MODULES_DIR must not redirect it.
process.env.NODE_MODULES_DIR = '/envs/node/ts-v2-2.3.1/node_modules';
await import('./_client_ts_v2.mjs');
