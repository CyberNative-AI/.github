// mcp-stdio-cross-era entry point: pins the npm prefix /envs/node/ts-sdk-1.29.0 and runs _server_ts_sdk1.mjs.
// The prefix is baked in (not read from the environment) because SDK stdio client transports spawn
// servers with a filtered default environment, and an inherited NODE_MODULES_DIR must not redirect it.
process.env.NODE_MODULES_DIR = '/envs/node/ts-sdk-1.29.0/node_modules';
await import('./_server_ts_sdk1.mjs');
