ARG DOCKER_REGISTRY=ghcr.io
ARG VERSION=latest
FROM $DOCKER_REGISTRY/kagent-dev/kagent/kagent-adk:$VERSION

WORKDIR /app

COPY pyproject.toml pyproject.toml

RUN uv sync

COPY kagent_vision/ kagent_vision/
COPY README.md README.md

CMD ["kagent_vision"]
