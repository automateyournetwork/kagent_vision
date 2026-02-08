FROM node:24-bookworm-slim

RUN apt-get update && apt-get install -y \
    python3 python3-pip python3-venv ca-certificates curl \
    libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

RUN curl -LsSf https://astral.sh/uv/install.sh | sh && \
    mv /root/.local/bin/uv /usr/local/bin/uv && \
    mv /root/.local/bin/uvx /usr/local/bin/uvx

COPY --from=ghcr.io/agentgateway/agentgateway:0.10.2 /app/agentgateway /app/agentgateway

WORKDIR /app

COPY pyproject.toml pyproject.toml
RUN uv venv && uv pip install -r pyproject.toml

COPY vision_mcp/ vision_mcp/
COPY config.yaml config.yaml

CMD ["/app/agentgateway", "-f", "config.yaml"]
