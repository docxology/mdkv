import json
from pathlib import Path
import importlib
from unittest.mock import patch

from click.testing import CliRunner

from mdkv.cli import main


def test_cli_init_export_html_and_validate_error(tmp_path: Path):
    doc_path = tmp_path / "newdoc.mdkv"
    # init (covers init path)
    r = CliRunner().invoke(main, [
        "init",
        "--title",
        "X",
        "--author",
        "Y",
        "--out",
        str(doc_path),
    ])
    assert r.exit_code == 0 and doc_path.exists()

    # export html (covers export html branch)
    r2 = CliRunner().invoke(main, ["export", str(doc_path), "--html"])  
    assert r2.exit_code == 0 and "<h1" in r2.output
    # export markdown default branch
    r2b = CliRunner().invoke(main, ["export", str(doc_path)])
    assert r2b.exit_code == 0 and "# New Document" in r2b.output

    # validate error branch: remove primary track and expect SystemExit(1)
    # we simulate by saving a doc without primary via CLI update (rename then remove)
    # Instead simpler: write a bogus file and call validate expecting failure
    bad_path = tmp_path / "bad.mdkv"
    bad_path.write_bytes(b"PK\x03\x04bogus")
    r3 = CliRunner().invoke(main, ["validate", str(bad_path)])
    assert r3.exit_code != 0


def test_cli_gui_command_is_invoked(tmp_path: Path):
    # Patch on the actual module object to avoid name shadowing by the click Group
    cli_main_mod = importlib.import_module("mdkv.cli.main")
    with patch.object(cli_main_mod, "run_gui") as run_mock:
        r = CliRunner().invoke(main, ["gui", "--host", "127.0.0.1", "--port", "0"])  # port 0 ignored in our wrapper but invoked
        assert r.exit_code == 0
        run_mock.assert_called()


