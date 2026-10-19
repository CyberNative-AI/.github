# Coding-agent CLIs, pinned. Network is used only at build time.
FROM node:24.22.0-slim
RUN apt-get update && apt-get install -y --no-install-recommends procps python3 ca-certificates git && rm -rf /var/lib/apt/lists/*
RUN npm install -g --no-fund --no-audit \
    @openai/codex@0.163.0 \
    @opencode/cli@2.0.32 \
    @anthropic-ai/claude-code@2.1.302 \
    @google/gemini-cli@0.64.0 \
    @qwen-code/qwen-code@0.25.2 \
    @charmland/crush@0.98.1 \
    @kilocode/cli@7.8.12 \
    @github/copilot@1.0.98 \
 && npm install --prefix /opt/oc1 --no-fund --no-audit opencode-ai@1.19.3 \
 && ln -s /opt/oc1/node_modules/.bin/opencode /usr/local/bin/opencode1 \
 && npm cache clean --force
RUN useradd -m -u 1500 tester
USER tester
WORKDIR /home/tester
