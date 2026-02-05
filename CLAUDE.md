# Claude Code Instructions

Project-specific instructions for Claude Code when working on the Cloud Custodian MCP Documentation Server.

## Project Overview

This is an MCP (Model Context Protocol) server that provides semantic search and full-text access to Cloud Custodian documentation. It uses:
- FastMCP for the server framework
- SQLite FTS5 for full-text search with BM25 ranking
- docutils for parsing reStructuredText (RST) files
- Git sparse checkout for efficient repository cloning

## Key Architecture Decisions

### RST Parsing with Docutils

- Cloud Custodian docs use reStructuredText, not Markdown
- We use docutils visitor pattern to traverse document trees
- Code blocks are excluded from searchable content
- RST directives and roles are cleaned from indexed text

### Database Design

- SQLite FTS5 virtual table with Porter stemming
- BM25 ranking with weighted fields (title: 5.0, description: 2.0, content: 1.0)
- Section indexing for filtering by cloud provider (aws, azure, gcp, etc.)
- Triggers maintain FTS index automatically

### URL Generation

Cloud Custodian documentation URL pattern:
- Repository: `docs/source/aws/examples/s3.rst`
- URL: `https://cloudcustodian.io/docs/aws/examples/s3.html`
- Strip `source/` prefix and convert `.rst` → `.html`

## Development Workflow

### Before Making Changes

1. Read existing code to understand patterns
2. Check test coverage for the module
3. Run `make build` to ensure baseline passes

### Making Changes

1. Write tests first (TDD approach)
2. Implement feature in src/
3. Run `make test` frequently
4. Run `make format` before committing
5. Run `make build` before creating PR

### Testing Strategy

- Unit tests for parser, database, indexer
- Mock git operations in tests (use `unittest.mock.patch`)
- Create temporary RST files with `tmp_path` fixture
- Target >80% code coverage

## Common Tasks

### Adding New RST Parsing Features

1. Update `TextContentVisitor` or `MetadataVisitor` in `parser.py`
2. Add test in `tests/test_parser.py` with sample RST content
3. Handle edge cases (empty files, malformed RST)

### Modifying Search Behaviour

1. Update SQL query in `database.py`
2. Adjust BM25 weights if needed
3. Add test in `tests/test_database.py`

### Updating Indexer

1. Modify `indexer.py` for repository changes
2. Update git commands if Cloud Custodian repo structure changes
3. Test with `test_indexer.py` using mocked subprocess

### Adding New MCP Tools

1. Add tool function in `server.py` with `@mcp.tool()` decorator
2. Update tool descriptions
3. Test manually with `make run`

## Code Patterns

### Error Handling

Return `None` for parsing failures, don't raise exceptions:

```python
def parse_file(self, file_path: Path) -> Document | None:
    try:
        # Parse RST
        return document
    except Exception:
        return None  # Graceful failure
```

### Logging

Use appropriate log levels:

```python
logger.info("Cloning repository...")  # User-facing progress
logger.debug("Indexed: %s", doc.path)  # Detailed debug info
logger.warning("Failed to parse: %s", path)  # Recoverable errors
```

### Type Hints with Docutils

Docutils lacks type stubs, use `type: ignore` comments:

```python
import docutils.nodes  # type: ignore[import-untyped]

class MetadataVisitor(docutils.nodes.GenericNodeVisitor):  # type: ignore[misc]
    pass
```

## Testing Patterns

### Parser Tests

Create temp RST files:

```python
def test_parse_basic(parser: DocumentParser, temp_docs_dir: Path) -> None:
    rst_content = """
Title
=====

Content here.
"""
    file_path = temp_docs_dir / "test.rst"
    file_path.write_text(rst_content)
    doc = parser.parse_file(file_path, temp_docs_dir)
    assert doc is not None
```

### Database Tests

Use temporary database:

```python
@pytest.fixture
def db(tmp_path: Path) -> DocumentDatabase:
    db_path = tmp_path / "test.db"
    return DocumentDatabase(db_path)
```

### Indexer Tests

Mock git operations:

```python
@patch("subprocess.run")
def test_clone(mock_run: Mock, indexer: CloudCustodianDocsIndexer) -> None:
    indexer._clone_repository(target_path, "main", shallow=True)
    assert "git" in mock_run.call_args[0][0]
```

## British English

Use British spelling in all code and documentation:
- `initialise` not `initialize`
- `colour` not `color`
- `organise` not `organize`

## Docstring Style

Use Google-style docstrings:

```python
def search(self, query: str, limit: int = 10) -> list[SearchResult]:
    """Search documents using FTS5.

    Args:
        query: Search query string.
        limit: Maximum number of results.

    Returns:
        List of SearchResult instances ordered by relevance.
    """
```

## Makefile Commands

Frequently used commands:

```bash
make init       # Set up development environment
make test       # Run pytest with coverage
make build      # Full build (lint + typecheck + test)
make format     # Format code with ruff
make index      # Build documentation index
make run        # Run MCP server locally
```

## Git Commit Messages

Follow Conventional Commits:

```
feat: add support for GCP documentation section
fix: handle empty RST files gracefully
docs: update usage guide with Docker instructions
test: add tests for URL generation
refactor: simplify section extraction logic
```

## Common Issues

### Docutils Deprecation Warnings

Expected warnings from docutils about `OptionParser` deprecation. Suppress with:

```python
settings.report_level = 5  # Suppress warnings
```

### Test Coverage Below 80%

- Add tests for uncovered code paths
- Focus on parser edge cases (empty files, malformed RST)
- Test error handling branches

### Type Errors with Docutils

Use `type: ignore` comments as documented above.

### Git Clone Failures in Tests

Mock subprocess.run in tests to avoid actual git operations.

## Documentation Requirements

When adding features, update:

1. `README.md` - Quick start and overview
2. `USAGE.md` - Detailed usage instructions
3. `CODESTYLE.md` - Code patterns if introducing new patterns
4. Docstrings - For all public functions

## Dependencies

Core dependencies:
- `fastmcp>=2.0.0` - MCP server framework
- `docutils>=0.21.0` - RST parsing

Dev dependencies:
- `pytest>=8.0.0` - Testing
- `pytest-cov>=6.0.0` - Coverage
- `mypy>=1.13.0` - Type checking
- `ruff>=0.8.0` - Linting and formatting

## Performance Considerations

### Indexing

- Git sparse checkout reduces clone size
- Shallow clone with `--depth 1` for speed
- Index ~195 documents in 1-2 minutes

### Search

- SQLite FTS5 is fast for this scale
- BM25 ranking is efficient
- Queries complete in <50ms

### Memory

- Parser processes files one at a time
- Database uses connection pooling (context manager)
- Docker image ~50MB with indexed database

## Security Considerations

### SQL Injection

Always use parameterised queries:

```python
cursor = conn.execute("SELECT * FROM documents WHERE path = ?", (path,))
```

### Subprocess Execution

Use subprocess.run with list arguments (not shell=True):

```python
subprocess.run(["git", "clone", url, path], check=True)  # noqa: S603
```

### Input Validation

Cap user inputs:

```python
limit = min(max(1, limit), 50)  # Between 1 and 50
```

## Debugging

### Enable Debug Logging

```python
logging.basicConfig(level=logging.DEBUG)
```

### Test Single File

```bash
uv run pytest tests/test_parser.py::test_parse_basic_rst_file -vv
```

### Interactive Testing

```bash
make run  # Start server
# Send MCP tool calls via stdin
```

## Future Enhancements

Potential improvements to consider:

1. Add caching layer for frequently accessed documents
2. Support incremental index updates
3. Add relevance feedback mechanism
4. Implement query suggestions
5. Add support for code snippet extraction
6. Create summary/abstract extraction from RST

## Questions to Ask

When uncertain, check:

1. Is there existing code doing something similar?
2. Do tests cover this edge case?
3. Does it follow the existing patterns?
4. Is error handling appropriate?
5. Are type hints correct?
6. Is documentation updated?

## Resources

- Cloud Custodian Docs: https://cloudcustodian.io/docs/
- Docutils Documentation: https://docutils.sourceforge.io/
- SQLite FTS5: https://www.sqlite.org/fts5.html
- FastMCP: https://github.com/jlowin/fastmcp
- MCP Protocol: https://modelcontextprotocol.io/

## Code Review Checklist

Before submitting changes:

- [ ] Tests pass (`make test`)
- [ ] Linting passes (`make lint`)
- [ ] Type checking passes (`make typecheck`)
- [ ] Code formatted (`make format`)
- [ ] Coverage >80%
- [ ] Documentation updated
- [ ] Commit message follows convention
- [ ] British English used
- [ ] No security issues
