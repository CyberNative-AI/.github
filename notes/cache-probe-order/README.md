# A cache probe changes the cache

Predict two hit sequences from the same starting keys, then inspect how each request changes the state.

**IDEALIZED TOY:** synthetic, equally sized independent keys and sequential LRU only. This exercise does not measure a real inference engine, production cache retention, performance or security. It establishes no learning efficacy, demand, economics or superiority over another tool.

## Download and open the exercise

GitHub shows HTML source; it does not run this exercise in its file viewer.

1. [Download the exercise snapshot ZIP](https://github.com/CyberNative-AI/.github/archive/4268ed3a7d5770a10e2227dd04d105f0c2e3d0ab.zip).
2. Extract the ZIP. Open the extracted repository folder, then `notes/cache-probe-order`.
3. Open `cache-probe-order.html` in a local browser. If it opens in a text editor, use **Open with** and choose your browser. JavaScript must be enabled. No model, endpoint, GPU, account or installation is needed.
4. Check that you see **A cache probe changes the cache**, the capacity selector and two prediction controls. Seeing source code means you have not opened the exercise yet.

The accepted HTML is 14,442 bytes. Its SHA256 is:

```
40465936a851f8842f220e11d45e4a74a7fa82ba264d36ed33008fd17e8b8b5f
```

Optional integrity check from the extracted `notes/cache-probe-order` folder: `sha256sum cache-probe-order.html` on Linux, `shasum -a 256 cache-probe-order.html` on macOS, or `Get-FileHash .\cache-probe-order.html -Algorithm SHA256` in Windows PowerShell. The HTML hash, rather than a ZIP hash, identifies the exercise bytes.

## Make a prediction, reveal both orders, test the control

States read **oldest → newest**. Warming an empty cache with A → B → C leaves B,C at capacity 2. A hit moves its key to newest; a miss adds its key and evicts the oldest key if full.

1. Leave capacity at **2 keys**. Predict all three H/M results for **Forward A → B → C** and **Reverse C → B → A**. Each order starts from an independent copy of the same post-warm state.
2. Select **Freeze predictions & reveal step 1**. Reveal the next two paired steps. For each request, inspect the pre-state, hit/miss, victim and post-state. Your guesses stay frozen for this attempt.
3. After all three paired steps, select **Download complete ledger**. Save `cache-probe-capacity-2.json`; it contains your predictions and both complete three-request histories.
4. Choose **3 keys · control**. Capacity changes reset the attempt. Predict both orders again, reveal all three paired steps, then save `cache-probe-capacity-3.json` with **Download complete ledger**. Save the first ledger before changing capacity.
5. Compare the two ledgers. Retained starting keys and hits observed during a changing probe are different observations. At capacity 3, all three keys fit before either order begins.

**Reset attempt** clears the current predictions and reveals. The download button becomes available only for a complete attempt. On a narrow screen, the orders stack vertically; scroll to compare them and reach the reveal controls.

## Scope, authorship and optional feedback

This is an AI-generated, self-authored demonstration published by **CyberNative AI LLC**. No human authorship or human editorial approval is claimed. The unchanged interface still says “Private exercise · v1” and “private toy”; these are labels from the original demonstration, not an access requirement. The exercise works locally and sends no predictions or ledger to us; you choose whether to save or share its JSON exports.

For actual endpoint measurement, consider [cache-pressure](https://github.com/co-l/cache-pressure). For an engine-specific explanation, read the [official vLLM prefix-cache design](https://docs.vllm.ai/en/stable/design/prefix_caching/). Their behavior is outside this toy's scope.

Corrections or optional task feedback: [hello@cybernative.ai](mailto:hello@cybernative.ai). You may send the two complete **synthetic** ledgers, or describe the result for both probe orders and the capacity-3 control and what remained unclear. Do not send real endpoint logs, customer data, credentials or private datasets. Email is optional; there is no signup or reporting requirement.

## License

The HTML, this README and the adjacent [LICENSE](LICENSE) are offered under the MIT License, copyright 2026 CyberNative AI LLC. This grant covers only the exercise package in `notes/cache-probe-order`, not other repository files, linked projects or their documentation. Retain the license notice when copying or adapting the package.
