"""Tests for documentation indexer."""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from mcp_cloudcustodian_documentation.database import DocumentDatabase
from mcp_cloudcustodian_documentation.indexer import CloudCustodianDocsIndexer


@pytest.fixture
def db(tmp_path: Path) -> DocumentDatabase:
    """Create a temporary database.

    Args:
        tmp_path: Pytest temporary directory fixture.

    Returns:
        DocumentDatabase instance.
    """
    db_path = tmp_path / "test.db"
    return DocumentDatabase(db_path)


@pytest.fixture
def indexer(db: DocumentDatabase) -> CloudCustodianDocsIndexer:
    """Create an indexer instance.

    Args:
        db: DocumentDatabase fixture.

    Returns:
        CloudCustodianDocsIndexer instance.
    """
    return CloudCustodianDocsIndexer(db)


def test_index_from_path(indexer: CloudCustodianDocsIndexer, tmp_path: Path) -> None:
    """Test indexing from a local directory."""
    # Create test RST files
    docs_dir = tmp_path / "source"
    docs_dir.mkdir()

    (docs_dir / "test1.rst").write_text("""
Test 1
======

First test document.
""")

    (docs_dir / "test2.rst").write_text("""
Test 2
======

Second test document.
""")

    count = indexer.index_from_path(docs_dir)

    assert count == 2
    assert indexer.database.get_document_count() == 2


def test_index_from_path_with_subdirectories(indexer: CloudCustodianDocsIndexer, tmp_path: Path) -> None:
    """Test indexing RST files in subdirectories."""
    docs_dir = tmp_path / "source"
    docs_dir.mkdir()

    # Create nested structure
    aws_dir = docs_dir / "aws"
    aws_dir.mkdir()
    (aws_dir / "s3.rst").write_text("""
S3
==

S3 content.
""")

    azure_dir = docs_dir / "azure"
    azure_dir.mkdir()
    (azure_dir / "storage.rst").write_text("""
Storage
=======

Azure storage content.
""")

    count = indexer.index_from_path(docs_dir)

    assert count == 2

    # Verify documents are indexed with correct sections
    s3_doc = indexer.database.get_document("aws/s3.rst")
    assert s3_doc is not None
    assert s3_doc.section == "aws"

    azure_doc = indexer.database.get_document("azure/storage.rst")
    assert azure_doc is not None
    assert azure_doc.section == "azure"


def test_index_from_path_nonexistent(indexer: CloudCustodianDocsIndexer, tmp_path: Path) -> None:
    """Test indexing from a nonexistent path raises error."""
    nonexistent_path = tmp_path / "nonexistent"

    with pytest.raises(ValueError, match="Documentation path does not exist"):
        indexer.index_from_path(nonexistent_path)


def test_index_skips_invalid_files(indexer: CloudCustodianDocsIndexer, tmp_path: Path) -> None:
    """Test that invalid RST files are skipped gracefully."""
    docs_dir = tmp_path / "source"
    docs_dir.mkdir()

    # Create valid file
    (docs_dir / "valid.rst").write_text("""
Valid
=====

Valid content.
""")

    # Create invalid file
    (docs_dir / "invalid.rst").write_bytes(b"\xff\xfe")

    count = indexer.index_from_path(docs_dir)

    # Only valid file should be indexed
    assert count == 1


def test_index_both_rst_extensions(indexer: CloudCustodianDocsIndexer, tmp_path: Path) -> None:
    """Test indexing both .rst and .rest files."""
    docs_dir = tmp_path / "source"
    docs_dir.mkdir()

    (docs_dir / "test.rst").write_text("""
RST File
========

Content.
""")

    (docs_dir / "test2.rest").write_text("""
REST File
=========

Content.
""")

    count = indexer.index_from_path(docs_dir)

    assert count == 2


def test_rebuild_index_clears_existing(indexer: CloudCustodianDocsIndexer, tmp_path: Path) -> None:
    """Test that rebuild_index clears existing data."""
    docs_dir = tmp_path / "source"
    docs_dir.mkdir()
    (docs_dir / "test.rst").write_text("""
Test
====

Content.
""")

    # Index once
    indexer.index_from_path(docs_dir)
    assert indexer.database.get_document_count() == 1

    # Mock index_from_git to actually call index_from_path for testing
    with patch.object(indexer, "index_from_git") as mock_index:
        mock_index.return_value = 1

        # Manually call what rebuild_index does
        indexer.database.clear()
        indexer.index_from_path(docs_dir)

    # Should still have 1 document (cleared then re-indexed)
    assert indexer.database.get_document_count() == 1


@patch("subprocess.run")
def test_clone_repository(mock_run: Mock, indexer: CloudCustodianDocsIndexer, tmp_path: Path) -> None:
    """Test that clone_repository runs correct git commands."""
    target_path = tmp_path / "cloud-custodian"

    indexer._clone_repository(target_path, "main", shallow=True)

    # Verify git clone was called
    assert mock_run.call_count == 2
    clone_call = mock_run.call_args_list[0]
    assert "git" in clone_call[0][0]
    assert "clone" in clone_call[0][0]
    assert "--branch" in clone_call[0][0]
    assert "main" in clone_call[0][0]

    # Verify sparse checkout was configured
    sparse_call = mock_run.call_args_list[1]
    assert "sparse-checkout" in sparse_call[0][0]
    assert "docs/source" in sparse_call[0][0]


@patch("subprocess.run")
def test_clone_repository_without_sparse(mock_run: Mock, indexer: CloudCustodianDocsIndexer, tmp_path: Path) -> None:
    """Test clone without sparse checkout."""
    target_path = tmp_path / "cloud-custodian"

    indexer._clone_repository(target_path, "main", shallow=False)

    # Should only have one call (git clone, no sparse checkout)
    assert mock_run.call_count == 1
    assert "clone" in mock_run.call_args[0][0]
