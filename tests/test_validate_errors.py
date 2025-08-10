import pytest
from datetime import datetime

from mdkv.core.model import MDKVDocument
from mdkv.core.validate import validate_document, ValidationError


def test_validate_errors():
    d = MDKVDocument(title="", authors=[], created=datetime(2025, 1, 1))
    with pytest.raises(ValidationError):
        validate_document(d)


