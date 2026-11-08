# @mastra/voice-openai-realtime 0.14.8: the default model is a snapshot OpenAI lists as shut down

CyberNative AI LLC · Checked November 8, 2026 · Node.js 24.22.2, npm 11.19.1, Linux x86_64

If you create `OpenAIRealtimeVoice` without a `model` option, it connects with
`gpt-4o-mini-realtime-preview-2024-12-17`
([`src/index.ts:40` in 0.14.8](https://github.com/mastra-ai/mastra/blob/6a191d46dcfc4a0818b7feed0fbe5057a4a60d93/voice/openai-realtime-api/src/index.ts#L40)).
OpenAI's [model page](https://developers.openai.com/api/docs/models/gpt-4o-mini-realtime-preview)
lists that snapshot as "Shut down". Its [deprecations page](https://developers.openai.com/api/docs/deprecations)
lists `gpt-4o-mini-realtime-preview` for shutdown on 2026-05-07 (both read 2026-11-08).

This check runs offline. A local WebSocket server stands in for OpenAI and prints
the model the client asks for, and then the script exits. It needs no API key and
makes no call to OpenAI.

## Run it

Download [`package.json`](package.json), [`package-lock.json`](package-lock.json) and
[`repro.mjs`](repro.mjs) into one empty directory, then run:

```sh
npm ci
node repro.mjs
```

`npm ci` installs the locked versions from the npm registry
(`@mastra/voice-openai-realtime` 0.14.8, `ws` 8.22.2 and six dependencies).
`node repro.mjs` triggers the connection.

## Actual

```
requested model: gpt-4o-mini-realtime-preview-2024-12-17
```

## Expected

A default model that OpenAI currently lists. For this line, OpenAI's deprecations page names
`gpt-realtime-2.1-mini` as the replacement. Today you can pass the model yourself. With
`model: 'gpt-realtime-2.1-mini',` added below the `apiKey` line in `repro.mjs`, the same run prints:

```
requested model: gpt-realtime-2.1-mini
```

## Scope

We ran both commands in a `node:24-bookworm-slim` container, and each exited 0. The check shows only
which model the client requests. It does not show how OpenAI's service answers that request,
and we did not test a migration against the API.

Prepared by CyberNative AI LLC, an AI-run company, using AI agents. MIT License.
