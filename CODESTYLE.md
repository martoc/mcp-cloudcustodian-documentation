# Code Style Guide

This document outlines the coding standards and conventions for the Cloud Custodian MCP Documentation Server project.

## General Principles

- Follow PEP 8 guidelines for Python code
- Use British English in code, comments, and documentation
- Prefer explicit error handling over silent failures
- Write clear, self-documenting code
- Maintain high test coverage (target: >80%)

## Python Style

### Imports

Organise imports in the following order:

1. Standard library imports
2. Third-party library imports
3. Local application imports

```python
import logging
import re
from pathlib import Path

import docutils.parsers.rst

from mcp_cloudcustodian_documentation.models import Document
```

### Type Hints

Use type hints for all function and method signatures:

```python
def parse_file(self, file_path: Path, base_path: Path) -> Document | None:
    """Parse an RST file and extract metadata."""
    ...
```

### Docstrings

Use Google-style docstrings for all public functions, classes, and methods:

```python
def search(self, query: str, section: str | None = None, limit: int = 10) -> list[SearchResult]:
    """Search documents using FTS5.

    Args:
        query: Search query string.
        section: Optional section filter.
        limit: Maximum number of results.

    Returns:
        List of SearchResult instances ordered by relevance.

    Raises:
        ValueError: If limit is invalid.
    """
```

### Function and Variable Names

- Use `snake_case` for functions and variables
- Use `PascalCase` for classes
- Use `UPPER_CASE` for constants

```python
DEFAULT_DB_PATH = Path("data/cloudcustodian_docs.db")

class DocumentParser:
    def parse_file(self, file_path: Path) -> Document | None:
        relative_path = file_path.relative_to(base_path)
```

### Line Length

- Maximum line length: 120 characters
- Break long lines logically

```python
# Good
results = db.search(
    query="s3 encryption",
    section="aws",
    limit=10,
)

# Avoid
results = db.search(query="s3 encryption", section="aws", limit=10, verbose=True, include_description=True, filter_by_date=True)
```

## RST Parser Specifics

### Visitor Pattern

Use docutils visitor pattern for traversing document trees:

```python
class MetadataVisitor(docutils.nodes.GenericNodeVisitor):
    def visit_title(self, node: docutils.nodes.title) -> None:
        """Extract title from node."""
        self.title = node.astext()

    def default_visit(self, node: docutils.nodes.Node) -> None:
        """Default handler for unhandled nodes."""
        pass
```

### Error Handling

Handle parsing errors gracefully:

```python
try:
    document = self.parser.parse_file(file_path, docs_path)
    if document:
        self.database.upsert_document(document)
except Exception:
    logger.warning("Failed to parse: %s", file_path)
```

## Testing

### Test Organisation

- One test file per module: `test_parser.py`, `test_database.py`
- Use descriptive test names: `test_parse_basic_rst_file`
- Group related tests with fixtures

### Fixtures

Use pytest fixtures for common test setup:

```python
@pytest.fixture
def parser() -> DocumentParser:
    """Create a DocumentParser instance."""
    return DocumentParser()

@pytest.fixture
def temp_docs_dir(tmp_path: Path) -> Path:
    """Create a temporary docs directory."""
    docs_dir = tmp_path / "source"
    docs_dir.mkdir()
    return docs_dir
```

### Test Structure

Follow AAA pattern (Arrange, Act, Assert):

```python
def test_search_basic(db: DocumentDatabase) -> None:
    """Test basic search functionality."""
    # Arrange
    doc = Document(path="test.rst", title="Test", ...)
    db.upsert_document(doc)

    # Act
    results = db.search("Test")

    # Assert
    assert len(results) == 1
    assert results[0].title == "Test"
```

## Linting and Type Checking

### Ruff Configuration

The project uses Ruff for linting and formatting:

```bash
# Check code
make lint

# Format code
make format
```

Enabled lint rules:
- `E`: pycodestyle errors
- `F`: pyflakes
- `I`: isort (import sorting)
- `UP`: pyupgrade
- `D`: pydocstyle (docstrings)
- `N`: pep8-naming
- `S`: flake8-bandit (security)
- `B`: flake8-bugbear
- `C4`: flake8-comprehensions
- `RUF`: Ruff-specific rules

### Mypy Configuration

Strict type checking with mypy:

```bash
make typecheck
```

Configuration:
- `strict = true`: Enable all strict checks
- `warn_return_any = true`: Warn on returning Any
- `warn_unused_ignores = true`: Warn on unused type ignores

### Type Ignore Comments

Use `type: ignore` comments when necessary:

```python
import docutils.nodes  # type: ignore[import-untyped]

class MetadataVisitor(docutils.nodes.GenericNodeVisitor):  # type: ignore[misc]
    pass
```

## Documentation

### Code Comments

Use comments for complex logic:

```python
# Remove 'source/' prefix if present and convert .rst to .html
path_str = str(relative_path)
if path_str.startswith("source/"):
    path_str = path_str[7:]  # Remove 'source/' prefix
```

### README Structure

Maintain clear documentation:

1. Project overview
2. Features
3. Quick start
4. Installation instructions
5. Usage examples
6. Configuration
7. Development guide

### Documentation Updates

Update documentation when:
- Adding new features
- Changing APIs
- Modifying configuration
- Updating dependencies

## Git Practices

### Commit Messages

Follow Conventional Commits specification:

```
feat: add support for .rest file extension
fix: handle empty RST files gracefully
docs: update usage guide with examples
test: add tests for section extraction
refactor: simplify URL generation logic
```

### Branch Naming

Use descriptive branch names:
- `feature/add-gcp-support`
- `bugfix/fix-url-generation`
- `docs/update-usage-guide`

### Pull Requests

- One feature per PR
- Include tests for new code
- Update documentation
- Pass all CI checks

## Design Patterns

### Builder Pattern

Not currently used, but consider for complex object construction.

### Factory Pattern

Not currently used, but consider for parser instantiation variants.

### Visitor Pattern

Used extensively in RST parsing:

```python
class TextContentVisitor(docutils.nodes.GenericNodeVisitor):
    def visit_Text(self, node: docutils.nodes.Text) -> None:
        self._text_parts.append(node.astext())

    def visit_literal_block(self, node: docutils.nodes.literal_block) -> None:
        raise docutils.nodes.SkipNode  # Skip code blocks
```

## Error Handling

### Logging

Use appropriate log levels:

```python
logger.info("Cloning repository...")
logger.debug("Indexed: %s", document.path)
logger.warning("Failed to parse: %s", file_path)
logger.error("Database not found: %s", db_path)
```

### Exceptions

Raise specific exceptions:

```python
if not docs_path.exists():
    msg = f"Documentation path does not exist: {docs_path}"
    raise ValueError(msg)
```

### Graceful Degradation

Handle errors without crashing:

```python
try:
    document = self.parser.parse_file(file_path, base_path)
    if document:
        self.database.upsert_document(document)
except Exception:
    return None  # Skip invalid files
```

## Performance

### Database Queries

Use prepared statements and indexing:

```python
cursor = conn.execute(
    "SELECT * FROM documents WHERE path = ?",
    (path,),
)
```

### File Operations

Use pathlib for path operations:

```python
rst_files = list(docs_path.rglob("*.rst")) + list(docs_path.rglob("*.rest"))
```

### Memory Management

Use context managers for resources:

```python
@contextmanager
def _get_connection(self) -> Generator[sqlite3.Connection, None, None]:
    conn = sqlite3.connect(self.db_path)
    try:
        yield conn
    finally:
        conn.close()
```

## Security

### Input Validation

Validate user inputs:

```python
limit = min(max(1, limit), 50)  # Cap between 1 and 50
```

### SQL Injection Prevention

Use parameterised queries:

```python
# Good
conn.execute("SELECT * FROM documents WHERE path = ?", (path,))

# Bad (SQL injection risk)
conn.execute(f"SELECT * FROM documents WHERE path = '{path}'")
```

### Subprocess Execution

Use subprocess safely:

```python
subprocess.run(
    ["git", "clone", "--branch", branch, repo_url, str(target_path)],
    check=True,
    capture_output=True,
)  # noqa: S603
```

## Maintenance

### Dependency Updates

Regularly update dependencies:

```bash
make generate  # Update uv.lock
```

### Code Reviews

Review for:
- Correctness
- Test coverage
- Documentation
- Code style
- Performance
- Security

### Refactoring

Refactor when:
- Code is duplicated
- Functions are too long (>50 lines)
- Complexity is high
- Tests are difficult to write

## Tools

### Makefile Targets

Common development commands:

```bash
make init       # Initialise environment
make test       # Run tests
make lint       # Run linter
make format     # Format code
make typecheck  # Run type checker
make build      # Full build (lint + typecheck + test)
make index      # Build documentation index
make run        # Run MCP server
```

### Development Workflow

1. Create feature branch
2. Write failing test
3. Implement feature
4. Run `make build`
5. Update documentation
6. Commit with conventional message
7. Create pull request

## British English

Use British spelling throughout:

- Colour (not color)
- Organise (not organize)
- Initialise (not initialize)
- Behaviour (not behavior)
- Centre (not center)

Examples in code:

```python
def initialise_database(self) -> None:
    """Initialise database schema."""
    ...

def get_colour_scheme(self) -> dict[str, str]:
    """Retrieve colour configuration."""
    ...
```

## Conclusion

Following these guidelines ensures consistent, maintainable, and high-quality code. When in doubt:

1. Check existing code for patterns
2. Prioritise readability over cleverness
3. Write tests first
4. Document non-obvious decisions
5. Ask for code review
