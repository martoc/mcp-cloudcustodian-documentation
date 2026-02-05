# Usage Guide

Detailed instructions for using the Cloud Custodian Documentation MCP Server.

## Installation

### Docker (Recommended)

Pull and run the pre-built Docker image:

```bash
docker pull mcp-cloudcustodian-documentation
docker run -i --rm mcp-cloudcustodian-documentation
```

### Local Installation with uv

```bash
# Clone repository
git clone https://github.com/martoc/mcp-cloudcustodian-documentation
cd mcp-cloudcustodian-documentation

# Initialise environment
make init

# Build documentation index
make index
```

## MCP Client Configuration

### Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

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

For local installation:

```json
{
  "mcpServers": {
    "cloud-custodian-documentation": {
      "command": "uv",
      "args": [
        "--directory",
        "/absolute/path/to/mcp-cloudcustodian-documentation",
        "run",
        "mcp-cloudcustodian-documentation"
      ]
    }
  }
}
```

### Other MCP Clients

Configure your MCP client to run:
- Docker: `docker run -i --rm mcp-cloudcustodian-documentation`
- Local: `uv --directory /path/to/project run mcp-cloudcustodian-documentation`

## Search Examples

### Basic Search

Search for Cloud Custodian features:

```json
{
  "tool": "search_documentation",
  "arguments": {
    "query": "s3 bucket encryption"
  }
}
```

### Search with Section Filter

Search within specific cloud provider documentation:

```json
{
  "tool": "search_documentation",
  "arguments": {
    "query": "lambda function",
    "section": "aws"
  }
}
```

Available sections:
- `aws` - AWS resource policies
- `azure` - Azure resource policies
- `gcp` - Google Cloud resource policies
- `kubernetes` - Kubernetes resource policies
- `oci` - Oracle Cloud Infrastructure policies
- `quickstart` - Getting started guides
- `developer` - Development guides
- `tools` - Cloud Custodian tools

### Limit Results

Control the number of results returned:

```json
{
  "tool": "search_documentation",
  "arguments": {
    "query": "policy examples",
    "limit": 20
  }
}
```

Maximum limit: 50 results

## Reading Documentation

### Get Full Document

Retrieve complete documentation content using the path from search results:

```json
{
  "tool": "read_documentation",
  "arguments": {
    "path": "aws/examples/s3.rst"
  }
}
```

### Common Document Paths

- AWS Examples: `aws/examples/*.rst`
- Azure Examples: `azure/examples/*.rst`
- Quickstart: `quickstart/index.rst`
- Developer Guide: `developer/developer.rst`

## CLI Usage

### Build Index

Index Cloud Custodian documentation from GitHub:

```bash
# Default: main branch
uv run cloud-custodian-docs-index index

# Specific branch
uv run cloud-custodian-docs-index index --branch main

# Rebuild (clear and reindex)
uv run cloud-custodian-docs-index index --rebuild
```

### View Statistics

Check the number of indexed documents:

```bash
uv run cloud-custodian-docs-index stats
```

Output:
```
INFO:mcp_cloudcustodian_documentation.cli:Total indexed documents: 195
```

### Custom Database Location

Use a custom database file:

```bash
uv run cloud-custodian-docs-index --database /path/to/custom.db index
uv run cloud-custodian-docs-index --database /path/to/custom.db stats
```

## Advanced Usage

### Search Query Syntax

The search uses SQLite FTS5 with Porter stemming:

- **Stemming**: "policy" matches "policies", "policing"
- **Phrase search**: "s3 bucket" matches documents with both terms
- **Boolean AND**: Terms are AND'd by default
- **Relevance**: Results ranked by BM25 algorithm

### Section Filtering

Filter by cloud provider or documentation section:

```python
# AWS only
results = search_documentation("ec2 instance", section="aws")

# Azure only
results = search_documentation("storage account", section="azure")

# GCP only
results = search_documentation("compute engine", section="gcp")
```

### Integration with Claude

Example conversation with Claude using the MCP server:

**User:** "How do I create a policy to encrypt S3 buckets in Cloud Custodian?"

**Claude:** *Uses search_documentation tool with query "s3 bucket encryption policy"*

**Claude:** "I found documentation on S3 bucket encryption policies. Let me read the full example."

**Claude:** *Uses read_documentation tool with path from search results*

**Claude:** "Here's how to create a policy for S3 bucket encryption..."

## Troubleshooting

### Database Not Found

**Error:** `Database not found: data/cloudcustodian_docs.db`

**Solution:** Build the index:
```bash
make index
```

### Git Clone Fails

**Error:** Git clone operation fails

**Solutions:**
- Check internet connection
- Verify git is installed: `git --version`
- Try manual clone: `git clone https://github.com/cloud-custodian/cloud-custodian.git`

### Search Returns No Results

**Issue:** Search queries return empty results

**Solutions:**
- Rebuild index: `uv run cloud-custodian-docs-index index --rebuild`
- Check document count: `uv run cloud-custodian-docs-index stats`
- Try simpler query terms

### Docker Permission Issues

**Error:** Docker socket permission denied

**Solution:** Ensure Docker daemon is running and user has permission:
```bash
docker ps  # Test Docker access
```

### MCP Client Connection Issues

**Issue:** Claude Desktop doesn't detect the server

**Solutions:**
- Restart Claude Desktop after configuration changes
- Check JSON syntax in config file
- Verify command path is correct
- Check logs: `~/Library/Logs/Claude/`

## Performance

### Index Size

- Documents: ~195 RST files
- Database size: ~2-3 MB
- Index time: 1-2 minutes (first build)
- Memory usage: <100 MB

### Query Performance

- Search latency: <50ms for most queries
- Result retrieval: <10ms per document
- Concurrent queries: Supported via SQLite

### Docker Performance

Pre-built Docker image includes indexed database:
- No indexing required at runtime
- Instant startup
- Consistent query performance

## Best Practises

### Search Queries

1. **Use specific terms**: "s3 bucket encryption" vs "storage"
2. **Include cloud provider**: Add AWS/Azure/GCP in query
3. **Use section filter**: Narrow results to relevant provider
4. **Try variations**: "policy" and "policies" both work

### Integration Patterns

1. **Search first**: Use search to find relevant documents
2. **Read specific docs**: Retrieve full content for detailed info
3. **Cache paths**: Remember useful document paths
4. **Limit results**: Start with fewer results, increase if needed

### Development Workflow

1. **Local testing**: Use `make run` for interactive testing
2. **Rebuild index**: Update index after Cloud Custodian releases
3. **Test queries**: Verify search quality with representative queries
4. **Monitor performance**: Check query latency and result relevance

## Examples

### Example 1: Find S3 Encryption Policy

```python
# Search for S3 encryption
search_documentation(
    query="s3 bucket encryption policy",
    section="aws",
    limit=5
)

# Returns paths like "aws/examples/s3.rst"

# Read full documentation
read_documentation(path="aws/examples/s3.rst")
```

### Example 2: Azure Resource Management

```python
# Search Azure documentation
search_documentation(
    query="virtual machine management",
    section="azure",
    limit=10
)

# Read specific example
read_documentation(path="azure/examples/vm.rst")
```

### Example 3: General Policy Search

```python
# Broad search across all providers
search_documentation(
    query="tagging resources",
    limit=20
)

# Filter to AWS
search_documentation(
    query="tagging resources",
    section="aws",
    limit=10
)
```

## API Reference

### search_documentation(query, section, limit)

**Parameters:**
- `query` (str): Search terms
- `section` (str, optional): Section filter
- `limit` (int, optional): Max results (default: 10, max: 50)

**Returns:** JSON with search results

**Example Response:**
```json
{
  "query": "s3 encryption",
  "section_filter": "aws",
  "result_count": 3,
  "results": [
    {
      "title": "S3 Bucket Policies",
      "url": "https://cloudcustodian.io/docs/aws/examples/s3.html",
      "path": "aws/examples/s3.rst",
      "section": "aws",
      "snippet": "...encryption policies for S3 buckets...",
      "relevance_score": 15.3421
    }
  ]
}
```

### read_documentation(path)

**Parameters:**
- `path` (str): Relative document path

**Returns:** JSON with document content

**Example Response:**
```json
{
  "path": "aws/examples/s3.rst",
  "title": "S3 Bucket Policies",
  "description": "Managing S3 buckets with Cloud Custodian",
  "section": "aws",
  "url": "https://cloudcustodian.io/docs/aws/examples/s3.html",
  "content": "Full RST content..."
}
```

## Support

- GitHub Issues: https://github.com/martoc/mcp-cloudcustodian-documentation/issues
- Cloud Custodian Docs: https://cloudcustodian.io/docs/
- MCP Documentation: https://modelcontextprotocol.io/
