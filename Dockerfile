FROM python:3.12-slim

WORKDIR /app

# Install git for cloning cloud-custodian/cloud-custodian repository
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy project files
COPY pyproject.toml README.md ./
COPY src/ src/
COPY data/ data/

# Install dependencies
RUN uv sync --no-dev

# Build the index at container build time
RUN uv run cloud-custodian-docs-index index

# Run the MCP server
CMD ["uv", "run", "mcp-cloudcustodian-documentation"]
