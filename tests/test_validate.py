from datetime import datetime
import pytest

from mdkv.model import Track, MDKVDocument
from mdkv.validate import validate_document, ValidationError


def test_basic_validation_passes():
    doc = MDKVDocument(title="T", authors=["A"], created=datetime(2025, 1, 1))
    doc.add_track(Track("primary", "primary", "en", "tracks/primary.md", "Hello"))
    validate_document(doc)  # does not raise


def test_validation_fails_without_primary():
    doc = MDKVDocument(title="T", authors=["A"], created=datetime(2025, 1, 1))
    with pytest.raises(ValidationError):
        validate_document(doc)


def test_validation_duplicate_track_ids():
    doc = MDKVDocument(title="T", authors=["A"], created=datetime(2025, 1, 1))
    doc.add_track(Track("primary", "primary", "en", "tracks/primary.md", "Hello"))
    with pytest.raises(ValidationError):
        doc.add_track(Track("primary", "translation", "fr", "tracks/primary-fr.md", "Bonjour"))


