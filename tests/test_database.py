"""Tests for database operations."""

from pathlib import Path

import pytest

from mcp_cloudcustodian_documentation.database import DocumentDatabase
from mcp_cloudcustodian_documentation.models import Document


@pytest.fixture
def db(tmp_path: Path) -> DocumentDatabase:
    """Create a temporary database.

    Args:
        tmp_path: Pytest temporary directory fixture.

    Returns:
        DocumentDatabase instance with temporary database.
    """
    db_path = tmp_path / "test.db"
    return DocumentDatabase(db_path)


@pytest.fixture
def sample_document() -> Document:
    """Create a sample document for testing.

    Returns:
        Sample Document instance.
    """
    return Document(
        path="aws/s3.rst",
        title="S3 Bucket Policies",
        description="Managing S3 buckets with Cloud Custodian",
        section="aws",
        content="Cloud Custodian provides powerful policies for managing S3 buckets.",
        url="https://cloudcustodian.io/docs/aws/s3.html",
    )


def test_upsert_document(db: DocumentDatabase, sample_document: Document) -> None:
    """Test inserting a document."""
    db.upsert_document(sample_document)
    count = db.get_document_count()
    assert count == 1


def test_get_document(db: DocumentDatabase, sample_document: Document) -> None:
    """Test retrieving a document by path."""
    db.upsert_document(sample_document)
    doc = db.get_document("aws/s3.rst")

    assert doc is not None
    assert doc.path == "aws/s3.rst"
    assert doc.title == "S3 Bucket Policies"
    assert doc.section == "aws"


def test_get_nonexistent_document(db: DocumentDatabase) -> None:
    """Test retrieving a document that doesn't exist."""
    doc = db.get_document("nonexistent.rst")
    assert doc is None


def test_update_document(db: DocumentDatabase, sample_document: Document) -> None:
    """Test updating an existing document."""
    db.upsert_document(sample_document)

    # Update the document
    updated_doc = Document(
        path="aws/s3.rst",
        title="Updated S3 Policies",
        description="Updated description",
        section="aws",
        content="Updated content about S3 policies.",
        url="https://cloudcustodian.io/docs/aws/s3.html",
    )
    db.upsert_document(updated_doc)

    # Should still have only one document
    count = db.get_document_count()
    assert count == 1

    # Verify the update
    doc = db.get_document("aws/s3.rst")
    assert doc is not None
    assert doc.title == "Updated S3 Policies"
    assert doc.description == "Updated description"


def test_search_basic(db: DocumentDatabase) -> None:
    """Test basic search functionality."""
    # Insert test documents
    docs = [
        Document(
            path="aws/s3.rst",
            title="S3 Bucket Policies",
            description="S3 bucket management",
            section="aws",
            content="Manage S3 buckets with encryption and lifecycle policies.",
            url="https://cloudcustodian.io/docs/aws/s3.html",
        ),
        Document(
            path="aws/ec2.rst",
            title="EC2 Instance Policies",
            description="EC2 instance management",
            section="aws",
            content="Manage EC2 instances with tagging and termination policies.",
            url="https://cloudcustodian.io/docs/aws/ec2.html",
        ),
    ]
    for doc in docs:
        db.upsert_document(doc)

    # Search for S3
    results = db.search("S3")
    assert len(results) == 1
    assert results[0].title == "S3 Bucket Policies"


def test_search_with_stemming(db: DocumentDatabase) -> None:
    """Test search with stemming support."""
    doc = Document(
        path="test.rst",
        title="Policy Examples",
        description="Multiple policies",
        section="examples",
        content="Cloud Custodian policies for managing resources.",
        url="https://cloudcustodian.io/docs/test.html",
    )
    db.upsert_document(doc)

    # "policy" should match "policies" due to stemming
    results = db.search("policy")
    assert len(results) == 1
    assert "policies" in results[0].snippet.lower() or "policy" in results[0].snippet.lower()


def test_search_with_section_filter(db: DocumentDatabase) -> None:
    """Test search with section filtering."""
    docs = [
        Document(
            path="aws/s3.rst",
            title="AWS S3",
            description="AWS S3",
            section="aws",
            content="AWS S3 policies",
            url="https://cloudcustodian.io/docs/aws/s3.html",
        ),
        Document(
            path="azure/storage.rst",
            title="Azure Storage",
            description="Azure Storage",
            section="azure",
            content="Azure storage policies",
            url="https://cloudcustodian.io/docs/azure/storage.html",
        ),
    ]
    for doc in docs:
        db.upsert_document(doc)

    # Search with section filter
    results = db.search("storage", section="azure")
    assert len(results) == 1
    assert results[0].section == "azure"


def test_search_with_limit(db: DocumentDatabase) -> None:
    """Test search with result limit."""
    # Insert multiple documents
    for i in range(10):
        doc = Document(
            path=f"test{i}.rst",
            title=f"Test {i}",
            description=f"Test document {i}",
            section="test",
            content="Cloud Custodian test content",
            url=f"https://cloudcustodian.io/docs/test{i}.html",
        )
        db.upsert_document(doc)

    # Search with limit
    results = db.search("test", limit=5)
    assert len(results) == 5


def test_search_no_results(db: DocumentDatabase, sample_document: Document) -> None:
    """Test search with no matching results."""
    db.upsert_document(sample_document)
    results = db.search("nonexistent_term_xyz")
    assert len(results) == 0


def test_clear_database(db: DocumentDatabase, sample_document: Document) -> None:
    """Test clearing all documents."""
    db.upsert_document(sample_document)
    assert db.get_document_count() == 1

    db.clear()
    assert db.get_document_count() == 0


def test_get_document_count_empty(db: DocumentDatabase) -> None:
    """Test document count on empty database."""
    count = db.get_document_count()
    assert count == 0


def test_sanitise_query() -> None:
    """Test FTS5 query sanitisation."""
    # Simple queries should not be modified
    assert DocumentDatabase._sanitise_query("simple") == "simple"
    assert DocumentDatabase._sanitise_query("test query") == "test query"
    assert DocumentDatabase._sanitise_query("S3") == "S3"

    # Queries with periods should be wrapped in quotes
    assert DocumentDatabase._sanitise_query("s3.bucket") == '"s3.bucket"'
    assert DocumentDatabase._sanitise_query("test.file.name") == '"test.file.name"'

    # Queries with parentheses should be wrapped
    assert DocumentDatabase._sanitise_query("test (value)") == '"test (value)"'

    # Queries with asterisks should be wrapped
    assert DocumentDatabase._sanitise_query("test*") == '"test*"'

    # Queries with colons should be wrapped
    assert DocumentDatabase._sanitise_query("field:value") == '"field:value"'

    # Queries with hyphens should be wrapped (regression test for "no such column" error)
    assert DocumentDatabase._sanitise_query("marked-for-op") == '"marked-for-op"'
    assert DocumentDatabase._sanitise_query("marked-for-op tag filter") == '"marked-for-op tag filter"'
    assert DocumentDatabase._sanitise_query("auto-tag-user") == '"auto-tag-user"'

    # Queries with existing quotes should be escaped and wrapped
    assert DocumentDatabase._sanitise_query('test "quoted"') == '"test ""quoted"""'

    # Queries with boolean operators should be wrapped
    assert DocumentDatabase._sanitise_query("test AND content") == '"test AND content"'
    assert DocumentDatabase._sanitise_query("test OR content") == '"test OR content"'
    assert DocumentDatabase._sanitise_query("NOT asterisks") == '"NOT asterisks"'
    assert DocumentDatabase._sanitise_query("test and content") == '"test and content"'


def test_search_relevance_ordering(db: DocumentDatabase) -> None:
    """Test that search results are ordered by relevance."""
    docs = [
        Document(
            path="high.rst",
            title="S3 Bucket S3 S3",
            description="S3 bucket management",
            section="aws",
            content="S3 S3 S3 buckets",
            url="https://cloudcustodian.io/docs/high.html",
        ),
        Document(
            path="low.rst",
            title="EC2 Instance",
            description="EC2 management",
            section="aws",
            content="Some content mentioning S3 once",
            url="https://cloudcustodian.io/docs/low.html",
        ),
    ]
    for doc in docs:
        db.upsert_document(doc)

    results = db.search("S3")
    assert len(results) == 2
    # Document with more S3 mentions should rank higher
    assert results[0].path == "high.rst"
    assert results[1].path == "low.rst"


def test_search_with_special_characters(db: DocumentDatabase) -> None:
    """Test search with FTS5 special characters like periods."""
    doc = Document(
        path="aws/s3.rst",
        title="S3 Configuration",
        description="Configure S3 buckets",
        section="aws",
        content="Use s3.bucket.name for configuration",
        url="https://cloudcustodian.io/docs/aws/s3.html",
    )
    db.upsert_document(doc)

    # Search with period (FTS5 special character)
    results = db.search("s3.bucket")
    assert len(results) >= 0  # Should not raise syntax error

    # Search with quotes
    results = db.search('"s3 bucket"')
    assert len(results) >= 0  # Should not raise syntax error


def test_search_with_sql_keywords(db: DocumentDatabase) -> None:
    """Test search with SQL reserved keywords."""
    doc = Document(
        path="test.rst",
        title="Group Policies",
        description="Policy groups",
        section="examples",
        content="Use group to organise policies",
        url="https://cloudcustodian.io/docs/test.html",
    )
    db.upsert_document(doc)

    # Search with SQL keyword
    results = db.search("group")
    assert len(results) == 1
    assert "group" in results[0].snippet.lower() or "Group" in results[0].snippet


def test_search_with_other_special_characters(db: DocumentDatabase) -> None:
    """Test search with various FTS5 special characters."""
    doc = Document(
        path="test.rst",
        title="Special Characters",
        description="Test special chars",
        section="test",
        content="Content with (parentheses) and * asterisks",
        url="https://cloudcustodian.io/docs/test.html",
    )
    db.upsert_document(doc)

    # These should not raise syntax errors
    test_queries = [
        "test*",
        "(parentheses)",
        "test AND content",
        "test OR content",
        "NOT asterisks",
    ]

    for query in test_queries:
        results = db.search(query)
        assert isinstance(results, list)  # Should not raise syntax error


def test_search_with_hyphens(db: DocumentDatabase) -> None:
    """Test search with hyphens in query (regression test for column syntax error)."""
    doc = Document(
        path="aws/examples.rst",
        title="Marked for Operation Examples",
        description="Using marked-for-op action",
        section="aws",
        content="The marked-for-op action allows tagging resources for future operations. "
        "Use the tag filter to identify resources.",
        url="https://cloudcustodian.io/docs/aws/examples.html",
    )
    db.upsert_document(doc)

    # This query previously caused "no such column: for" error
    results = db.search("marked-for-op tag filter")
    assert isinstance(results, list)  # Should not raise syntax error
    assert len(results) >= 0

    # Test various hyphenated queries
    hyphenated_queries = [
        "marked-for-op",
        "auto-tag-user",
        "real-time-events",
        "some-hyphenated-term tag filter",
    ]

    for query in hyphenated_queries:
        results = db.search(query)
        assert isinstance(results, list)  # Should not raise syntax error
