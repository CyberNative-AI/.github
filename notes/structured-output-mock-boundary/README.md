# A mock can bypass your structured-output validator

If `FakeListChatModel` returns `{"category":"banana"}` despite a Zod enum, check the mock before concluding that the provider integration ignores your schema.

A [current NestJS/LangChain example](https://github.com/nestjsninja/nestjs-langchain/blob/d000c31b9d7b0c501a4c07fff4d5ccd4939ca0d7/README.md) says structured output parses without validation. Its [triage tests](https://github.com/nestjsninja/nestjs-langchain/blob/d000c31b9d7b0c501a4c07fff4d5ccd4939ca0d7/src/triage/_test/triage.service.spec.ts) use `FakeListChatModel`. That distinction changes what the test establishes.

We checked `@langchain/core` 1.2.12 and Zod 4.6.5, matching the example's locked core and Zod versions. The fake's `withStructuredOutput` returns tool arguments or parses JSON; it does not use the supplied schema. The core content-parser factory takes a different path: Zod selects a validating parser, while a plain JSON Schema object selects JSON parsing without schema validation. [Current source](https://github.com/langchain-ai/langchainjs/blob/62d6d6ba06aa2d99b35dfbabc0a262eeac9ed8ec/libs/langchain-core/src/utils/testing/chat_models.ts), [parser factory](https://github.com/langchain-ai/langchainjs/blob/62d6d6ba06aa2d99b35dfbabc0a262eeac9ed8ec/libs/langchain-core/src/language_models/structured_output.ts).

Our local synthetic check produced these results:

- A valid category passed all three paths.
- An invalid category and a missing category passed the fake and the plain-JSON-Schema content parser. The Zod content parser rejected both.
- Malformed JSON failed all three paths.

The reader action: identify the class, package version, schema representation and output method behind a test. A service test with a fake can prove that your service rejects bad values. It cannot, by itself, establish how a provider integration validates them. LangChain's [model documentation](https://docs.langchain.com/oss/javascript/langchain/models#structured-output) describes runtime validation for Zod and Standard Schema, and manual validation for plain JSON Schema.

## Rerun without a model account

In a new directory, install the two exact packages, save the script below as `probe.mjs`, and run it:

```sh
npm install --ignore-scripts --no-audit --no-fund --save-exact @langchain/core@1.2.12 zod@4.6.5
node probe.mjs
```

The script asserts each expected acceptance result and prints the observed values or error classes. Our run used Node 24.21.0.

```js
import assert from 'node:assert/strict';
import { FakeListChatModel } from '@langchain/core/utils/testing';
import { createContentParser } from '@langchain/core/language_models/structured_output';
import { z } from 'zod';

const schema = z.object({ category: z.enum(['delivery', 'other']) });
const jsonSchema = { type: 'object', properties: {
  category: { type: 'string', enum: ['delivery', 'other'] }
}, required: ['category'] };
const cases = [
  ['valid', '{"category":"delivery"}', [true, true, true]],
  ['wrong-enum', '{"category":"banana"}', [true, false, true]],
  ['missing-field', '{}', [true, false, true]],
  ['malformed-json', '{', [false, false, false]],
];
const rows = [];
for (const [name, text, expected] of cases) {
  const paths = [
    ['fake+zod', () => new FakeListChatModel({ responses: [text] })
      .withStructuredOutput(schema).invoke('synthetic test')],
    ['content-parser+zod', () => createContentParser(schema).invoke(text)],
    ['content-parser+json-schema', () => createContentParser(jsonSchema).invoke(text)],
  ];
  for (let index = 0; index < paths.length; index++) {
    const [path, run] = paths[index];
    let accepted = false;
    let value;
    let error;
    try { value = await run(); accepted = true; }
    catch (caught) { error = caught.constructor.name; }
    assert.equal(accepted, expected[index], `${name}/${path}`);
    rows.push({ case: name, path, accepted, ...(accepted ? { value } : { error }) });
  }
}
console.log(JSON.stringify({ node: process.version,
  packages: { '@langchain/core': '1.2.12', zod: '4.6.5' },
  scope: 'synthetic fake model and core content parsers only; no provider/API/agent runtime',
  rows }, null, 2));
```

**Scope:** this checks a fake model and core content parsers, not a live provider, model quality, tool authorization or the `createAgent` loop. It does not prove that every adapter follows the same path, or that schema validation makes an action safe. Keep application-specific checks and error handling at the boundary; test the selected integration separately when its behavior matters.

Prepared with AI assistance. Publisher: CyberNative AI LLC. Corrections: hello@cybernative.ai.
