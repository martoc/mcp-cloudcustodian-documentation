# Cloud Custodian Documentation MCP Server

A Model Context Protocol (MCP) server that provides semantic search and full-text access to Cloud Custodian documentation. Built with FastMCP and SQLite FTS5 for high-performance documentation retrieval.

## Features

- **Full-text search** using SQLite FTS5 with BM25 ranking
- **Section filtering** for cloud providers (AWS, Azure, GCP, Kubernetes, OCI)
- **Pre-built Docker image** with indexed documentation
- **Fast queries** with stemming support (e.g., "policy" matches "policies")
- **Complete documentation access** including examples and API references

## Quick Start

### Using Docker (Recommended)

The Docker image includes pre-indexed Cloud Custodian documentation:

```bash
docker pull mcp-cloudcustodian-documentation
docker run -i --rm mcp-cloudcustodian-documentation
```

### Using uv

```bash
# Clone repository
git clone https://github.com/martoc/mcp-cloudcustodian-documentation
cd mcp-cloudcustodian-documentation

# Initialise environment
make init

# Build documentation index
make index

# Run server
make run
```

## MCP Client Configuration

Add to your MCP client settings (e.g., Claude Desktop):

### Docker Configuration

```json
{
  "mcpServers": {
    "cloud-custodian-documentation": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "mcp-cloudcustodian-documentation"]
    }
  }
}
```

### Local Installation Configuration

```json
{
  "mcpServers": {
    "cloud-custodian-documentation": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/mcp-cloudcustodian-documentation",
        "run",
        "mcp-cloudcustodian-documentation"
      ]
    }
  }
}
```

## Available Tools

### search_documentation

Search Cloud Custodian documentation by keyword query.

**Parameters:**
- `query` (string, required): Search terms with stemming support
- `section` (string, optional): Filter by section
  - Common sections: `aws`, `azure`, `gcp`, `kubernetes`, `oci`, `quickstart`, `developer`, `tools`
- `limit` (integer, optional): Maximum results (default: 10, max: 50)

**Example:**
```json
{
  "query": "s3 bucket encryption policy",
  "section": "aws",
  "limit": 5
}
```

### read_documentation

Read the full content of a specific documentation page.

**Parameters:**
- `path` (string, required): Relative path from search results (e.g., `aws/examples/s3.rst`)

**Example:**
```json
{
  "path": "aws/examples/s3.rst"
}
```

## CLI Commands

### Index Documentation

```bash
# Build index from GitHub (default: main branch)
uv run cloud-custodian-docs-index index

# Rebuild index (clear and reindex)
uv run cloud-custodian-docs-index index --rebuild

# Index specific branch
uv run cloud-custodian-docs-index index --branch main
```

### Show Statistics

```bash
uv run cloud-custodian-docs-index stats
```

## Development

### Requirements

- Python 3.12+
- uv 0.5.0+
- Git

### Setup

```bash
# Initialise environment
make init

# Run tests
make test

# Run full build (lint, typecheck, test)
make build

# Format code
make format
```

### Project Structure

```
mcp-cloudcustodian-documentation/
├── src/mcp_cloudcustodian_documentation/
│   ├── server.py       # FastMCP server with tools
│   ├── database.py     # SQLite FTS5 database
│   ├── parser.py       # RST document parser
│   ├── indexer.py      # Git repository indexer
│   ├── cli.py          # CLI commands
│   └── models.py       # Data structures
├── tests/              # pytest test suite
├── data/               # SQLite database (gitignored)
├── pyproject.toml      # Dependencies and configuration
├── Makefile            # Build automation
└── Dockerfile          # Container with pre-built index
```

## Architecture

### RST Document Parsing

Cloud Custodian documentation uses reStructuredText (RST) format. The parser:

1. Uses `docutils` to parse RST into a document tree
2. Extracts metadata (title, description) using visitor pattern
3. Extracts searchable text content (excluding code blocks)
4. Generates cloudcustodian.io URLs from file paths

### Search Implementation

- **SQLite FTS5** with Porter stemming for full-text search
- **BM25 ranking** with tuned weights (title: 5.0, description: 2.0, content: 1.0)
- **Section indexing** for fast filtering by cloud provider
- **Snippet generation** with highlighted matches

### Data Flow

```
GitHub Repo → Git Sparse Checkout → RST Parser → SQLite FTS5 → FastMCP Server
```

## Testing

```bash
# Run all tests with coverage
make test

# Run specific test file
uv run pytest tests/test_parser.py

# Run with verbose output
uv run pytest -vv
```

## Docker

### Build Image

```bash
make docker-build
```

The build process:
1. Installs dependencies with uv
2. Clones Cloud Custodian repository (docs only)
3. Indexes all RST files into SQLite database
4. Creates image with pre-built index (~195 documents)

### Run Container

```bash
make docker-run
```

## Troubleshooting

### Database not found

Run the indexer to build the database:
```bash
make index
```

### Git clone fails

Ensure git is installed and you have network access:
```bash
git --version
```

### Search returns no results

Rebuild the index:
```bash
uv run cloud-custodian-docs-index index --rebuild
```

## Documentation

- [USAGE.md](USAGE.md) - Detailed usage instructions
- [CODESTYLE.md](CODESTYLE.md) - Coding standards
- [Cloud Custodian Documentation](https://cloudcustodian.io/docs/)

## Licence

MIT Licence - see [LICENCE](LICENCE) file for details.

## Contributing

Contributions are welcome. Please ensure:
- All tests pass (`make test`)
- Code is formatted (`make format`)
- Type checking passes (`make typecheck`)
- Test coverage remains above 80%

## Related Projects

- [mcp-spark-documentation](https://github.com/martoc/mcp-spark-documentation) - MCP server for Apache Spark docs
- [FastMCP](https://github.com/jlowin/fastmcp) - FastMCP framework
- [Cloud Custodian](https://github.com/cloud-custodian/cloud-custodian) - Cloud resource management tool
