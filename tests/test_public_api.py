"""Tests for MDKVFormatError and MDKVFormatError in public API exports."""
from mdkv import MDKVFormatError
from mdkv.storage import MDKVFormatError as StorageMDKVFormatError


def test_mdkv_format_error_is_exported():
    assert MDKVFormatError is StorageMDKVFormatError
    assert issubclass(MDKVFormatError, Exception)


def test_mdkv_format_error_is_catchable():
    try:
        raise MDKVFormatError("test message")
    except MDKVFormatError as e:
        assert str(e) == "test message"
