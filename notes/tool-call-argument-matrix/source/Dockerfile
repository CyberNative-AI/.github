FROM python:3.12-slim
RUN pip install -q --no-cache-dir uv==0.8.22
ENV UV_NO_CACHE=1 CREWAI_DISABLE_TELEMETRY=true OTEL_SDK_DISABLED=true ANONYMIZED_TELEMETRY=false \
    LANGCHAIN_TRACING_V2=false DO_NOT_TRACK=1 LITELLM_LOCAL_MODEL_COST_MAP=True HF_HUB_OFFLINE=1
WORKDIR /opt
COPY req-*.txt /opt/
RUN for name in openai-agents langchain crewai smolagents pydantic-ai llama-index autogen strands google-adk; do \
      uv venv -q --python 3.12 /opt/venv-$name && \
      VIRTUAL_ENV=/opt/venv-$name uv pip install -q -r /opt/req-$name.txt || exit 1; \
    done
