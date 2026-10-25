# Third-party notices

## LiveCodeBench (MIT)

`src/judge.py` copies one string verbatim, `IMPORT_STRING`: the import header that
LiveCodeBench prepends to every solution. We took it from `import_string` in
`lcb_runner/evaluation/testing_util.py`, at LiveCodeBench commit `28fef95e`
(https://github.com/LiveCodeBench/LiveCodeBench/blob/28fef95e/lcb_runner/evaluation/testing_util.py).
The copy in GVS5H commit `707e2129` (`codebase/livecodebench/lcb_runner/evaluation/testing_util.py`)
carries the same string. LiveCodeBench's `testing_util.py` derives from
`eval/testing_util.py` in hendrycks/apps (MIT, Copyright (c) 2021 Dan Hendrycks). Both
licences are reproduced below. The rest of our judge and checkers is our own code.

```text
MIT License

Copyright (c) 2024 LiveCodeBench

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

```text
MIT License

Copyright (c) 2021 Dan Hendrycks

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## GVS5H run data (CC BY 4.0)

The `detail` fields in `out/verdicts*.jsonl` quote short, truncated excerpts of error
output and source lines from the stored solutions in GVS5H's `runs/` directory. We
selected and truncated them; we did not otherwise change them. That run data is licensed
under CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/). Credit, as the authors ask:

> Victor Gao, Vida Khosrowshahi, Ali Khosrowshahi, Xihao Sun, Juhyun Lee and
> Simon (Sang Won) Lee. *Zero-Shot Self-Orchestration with Ledger-Based Control
> Improves Coding in Language Models*. 2026. <https://github.com/slee-persis/GVS5H>

Copyright (c) 2026 Persis Capital Inc.

## Not included

This folder contains no benchmark problem statements and no tests. Those come from
LiveCodeBench's Hugging Face dataset and the original contest sites, under their own terms.
The commands in `README.md` download them.
