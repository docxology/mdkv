"""Tests for enhanced validation: warnings, path uniqueness, content heuristics."""
from datetime import datetime

import pytest

from mdkv.core.model import MDKVDocument, Track
from mdkv.core.validate import validate_document, ValidationIssue
from mdkv.core.errors import ValidationError


def _base_doc() -> MDKVDocument:
    d = MDKVDocument(title="T", authors=["A"], created=datetime(2025, 1, 1))
    d.add_track(Track("primary", "primary", "en", "tracks/primary.md", "content"))
    return d


def test_validate_passes_with_no_issues():
    doc = _base_doc()
    issues = validate_document(doc)
    assert issues == []


def test_validate_warns_on_empty_content():
    doc = _base_doc()
    doc.add_track(Track("notes", "commentary", None, "tracks/notes.md", "   "))
    issues = validate_document(doc)
    warns = [i for i in issues if i.level == "WARN"]
    assert any("empty content" in i.message for i in warns)


def test_validate_warns_on_code_track_without_fences():
    doc = _base_doc()
    doc.add_track(Track("code1", "code", "python", "tracks/code1.md", "print('hi')"))
    issues = validate_document(doc)
    warns = [i for i in issues if i.level == "WARN"]
    assert any("no fenced code blocks" in i.message for i in warns)


def test_validate_warns_on_translation_without_language():
    doc = _base_doc()
    doc.add_track(Track("trans", "translation", None, "tracks/trans.md", "bonjour"))
    issues = validate_document(doc)
    warns = [i for i in issues if i.level == "WARN"]
    assert any("no language set" in i.message for i in warns)


def test_validate_warns_on_multiple_primaries():
    doc = _base_doc()
    doc.add_track(Track("primary2", "primary", "en", "tracks/primary2.md", "content"))
    issues = validate_document(doc)
    warns = [i for i in issues if i.level == "WARN"]
    assert any("primary tracks" in i.message for i in warns)


def test_validate_warns_on_bad_version():
    doc = _base_doc()
    doc.version = "not-a-version"
    issues = validate_document(doc)
    warns = [i for i in issues if i.level == "WARN"]
    assert any("version" in i.message for i in warns)


def test_validate_good_version_no_warning():
    doc = _base_doc()
    doc.version = "1.2.3"
    issues = validate_document(doc)
    warns = [i for i in issues if i.level == "WARN"]
    assert not any("version" in i.message for i in warns)


def test_validation_issue_has_track_id():
    doc = _base_doc()
    doc.add_track(Track("notes", "commentary", None, "tracks/notes.md", ""))
    issues = validate_document(doc)
    empty_issue = [i for i in issues if "empty content" in i.message]
    assert empty_issue and empty_issue[0].track_id == "notes"
