from pathlib import Path

import pytest
from click.testing import CliRunner

from mdkv.cli import main
from mdkv.gui.server import run, state


@pytest.mark.parametrize("exists", [False, True])
def test_gui_bad_fixture_is_a_clean_cli_failure(tmp_path: Path, exists: bool):
    path = tmp_path / "invalid.mdkv"
    original = b"not a ZIP container"
    if exists:
        path.write_bytes(original)
    result = CliRunner().invoke(main, ["gui", "--path", str(path)])
    assert result.exit_code == 1
    assert "Traceback" not in result.output
    assert path.exists() is exists
    if exists:
        assert path.read_bytes() == original


@pytest.mark.parametrize("host", ["0.0.0.0", "::", "evil.example", "127.0.0.2"])
def test_gui_rejects_remote_binding_before_opening_a_document(tmp_path: Path, host: str):
    path = tmp_path / "invalid.mdkv"
    path.write_bytes(b"not a ZIP container")
    original_path, original_doc = state.path, state.doc
    with pytest.raises(ValueError, match="loopback"):
        run(host=host, path=str(path))
    assert state.path is original_path and state.doc is original_doc
    result = CliRunner().invoke(main, ["gui", "--host", host, "--path", str(path)])
    assert result.exit_code == 2
    assert "Traceback" not in result.output
