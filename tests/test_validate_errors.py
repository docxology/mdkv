from datetime import datetime

import pytest

from mdkv.core.model import MDKVDocument
from mdkv.core.validate import ValidationError, validate_document


def test_validate_errors():
    d = MDKVDocument(title="", authors=[], created=datetime(2025, 1, 1))
    with pytest.raises(ValidationError):
        validate_document(d)


