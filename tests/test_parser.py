"""Tests for RST document parser."""

from pathlib import Path

import pytest

from mcp_cloudcustodian_documentation.parser import DocumentParser


@pytest.fixture
def parser() -> DocumentParser:
    """Create a DocumentParser instance.

    Returns:
        DocumentParser instance.
    """
    return DocumentParser()


@pytest.fixture
def temp_docs_dir(tmp_path: Path) -> Path:
    """Create a temporary docs directory.

    Args:
        tmp_path: Pytest temporary directory fixture.

    Returns:
        Path to temporary docs directory.
    """
    docs_dir = tmp_path / "source"
    docs_dir.mkdir()
    return docs_dir


def test_parse_basic_rst_file(parser: DocumentParser, temp_docs_dir: Path) -> None:
    """Test parsing a basic RST file."""
    rst_content = """
Getting Started
===============

Cloud Custodian is a tool for managing cloud resources.

This is the second paragraph.
"""
    file_path = temp_docs_dir / "getting-started.rst"
    file_path.write_text(rst_content)

    doc = parser.parse_file(file_path, temp_docs_dir)

    assert doc is not None
    assert doc.title == "Getting Started"
    assert "Cloud Custodian" in doc.content
    assert doc.section == "root"
    assert doc.url == "https://cloudcustodian.io/docs/getting-started.html"


def test_extract_title_from_section(parser: DocumentParser, temp_docs_dir: Path) -> None:
    """Test extracting title from RST section header."""
    rst_content = """
AWS S3 Policies
===============

Managing S3 buckets with Cloud Custodian.
"""
    file_path = temp_docs_dir / "aws-s3.rst"
    file_path.write_text(rst_content)

    doc = parser.parse_file(file_path, temp_docs_dir)

    assert doc is not None
    assert doc.title == "AWS S3 Policies"


def test_extract_description_from_paragraph(parser: DocumentParser, temp_docs_dir: Path) -> None:
    """Test extracting description from first paragraph."""
    rst_content = """
Title
=====

This is the description paragraph.

This is another paragraph.
"""
    file_path = temp_docs_dir / "test.rst"
    file_path.write_text(rst_content)

    doc = parser.parse_file(file_path, temp_docs_dir)

    assert doc is not None
    assert doc.description == "This is the description paragraph."


def test_fallback_title_from_filename(parser: DocumentParser, temp_docs_dir: Path) -> None:
    """Test fallback to filename when no title is found."""
    rst_content = """
Just some content without a title.
"""
    file_path = temp_docs_dir / "my-test-file.rst"
    file_path.write_text(rst_content)

    doc = parser.parse_file(file_path, temp_docs_dir)

    assert doc is not None
    assert doc.title == "My Test File"


def test_compute_url(parser: DocumentParser, temp_docs_dir: Path) -> None:
    """Test URL generation for different file paths."""
    rst_content = """
Test
====

Content.
"""
    # Test RST file in subdirectory
    aws_dir = temp_docs_dir / "aws"
    aws_dir.mkdir()
    file_path = aws_dir / "s3.rst"
    file_path.write_text(rst_content)

    doc = parser.parse_file(file_path, temp_docs_dir)

    assert doc is not None
    assert doc.url == "https://cloudcustodian.io/docs/aws/s3.html"


def test_skip_code_blocks(parser: DocumentParser, temp_docs_dir: Path) -> None:
    """Test that code blocks are excluded from content."""
    rst_content = """
Example Policy
==============

Here is a policy example:

.. code-block:: yaml

    policies:
      - name: test
        resource: s3

This text should be included.
"""
    file_path = temp_docs_dir / "example.rst"
    file_path.write_text(rst_content)

    doc = parser.parse_file(file_path, temp_docs_dir)

    assert doc is not None
    assert "policies:" not in doc.content
    assert "This text should be included" in doc.content


def test_clean_rst_directives(parser: DocumentParser, temp_docs_dir: Path) -> None:
    """Test that RST directives are cleaned from content."""
    rst_content = """
Title
=====

.. note::
   This is a note.

.. warning::
   This is a warning.

Normal content here.
"""
    file_path = temp_docs_dir / "directives.rst"
    file_path.write_text(rst_content)

    doc = parser.parse_file(file_path, temp_docs_dir)

    assert doc is not None
    assert ".. note::" not in doc.content
    assert ".. warning::" not in doc.content
    assert "Normal content here" in doc.content


def test_clean_rst_roles(parser: DocumentParser, temp_docs_dir: Path) -> None:
    """Test that RST roles are cleaned from content."""
    rst_content = """
Title
=====

See :doc:`other-document` for more information.

Use :ref:`section-reference` to link sections.
"""
    file_path = temp_docs_dir / "roles.rst"
    file_path.write_text(rst_content)

    doc = parser.parse_file(file_path, temp_docs_dir)

    assert doc is not None
    assert ":doc:" not in doc.content
    assert ":ref:" not in doc.content


def test_extract_section_from_path(parser: DocumentParser, temp_docs_dir: Path) -> None:
    """Test section extraction from file path."""
    rst_content = """
Test
====

Content.
"""
    # Test AWS section
    aws_dir = temp_docs_dir / "aws" / "examples"
    aws_dir.mkdir(parents=True)
    file_path = aws_dir / "s3.rst"
    file_path.write_text(rst_content)

    doc = parser.parse_file(file_path, temp_docs_dir)

    assert doc is not None
    assert doc.section == "aws"


def test_parse_rst_with_tables(parser: DocumentParser, temp_docs_dir: Path) -> None:
    """Test parsing RST with tables."""
    rst_content = """
Resources
=========

+----------+-------------+
| Resource | Description |
+==========+=============+
| s3       | S3 buckets  |
+----------+-------------+
| ec2      | EC2 inst.   |
+----------+-------------+

Content after table.
"""
    file_path = temp_docs_dir / "tables.rst"
    file_path.write_text(rst_content)

    doc = parser.parse_file(file_path, temp_docs_dir)

    assert doc is not None
    assert "Resources" in doc.content
    assert "Content after table" in doc.content


def test_parse_rest_extension(parser: DocumentParser, temp_docs_dir: Path) -> None:
    """Test parsing .rest files (alternative RST extension)."""
    rst_content = """
Alternative Extension
=====================

This file uses .rest extension.
"""
    file_path = temp_docs_dir / "alternative.rest"
    file_path.write_text(rst_content)

    doc = parser.parse_file(file_path, temp_docs_dir)

    assert doc is not None
    assert doc.title == "Alternative Extension"
    assert doc.url == "https://cloudcustodian.io/docs/alternative.html"


def test_parse_invalid_rst(parser: DocumentParser, temp_docs_dir: Path) -> None:
    """Test that invalid RST files return None gracefully."""
    file_path = temp_docs_dir / "invalid.rst"
    # Create a file that will cause parsing issues
    file_path.write_bytes(b"\xff\xfe")

    doc = parser.parse_file(file_path, temp_docs_dir)

    assert doc is None


def test_parse_empty_file(parser: DocumentParser, temp_docs_dir: Path) -> None:
    """Test parsing an empty RST file."""
    file_path = temp_docs_dir / "empty.rst"
    file_path.write_text("")

    doc = parser.parse_file(file_path, temp_docs_dir)

    assert doc is not None
    assert doc.title == "Empty"  # Fallback to filename
