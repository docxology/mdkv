from __future__ import annotations

"""Comprehensive tests targeting full CLI coverage (pandoc export, batch errors, license, etc.)."""

import json
from datetime import UTC, datetime
from pathlib import Path

from click.testing import CliRunner

from mdkv.cli import main
from mdkv.core.model import MDKVDocument, Track
from mdkv.storage import save_mdkv


def _make_doc(tmp_path: Path) -> Path:
    p = tmp_path / "doc.mdkv"
    doc = MDKVDocument(title="Doc", authors=["A"], created=datetime.now(UTC))
    doc.add_track(Track("primary", "primary", "en", "tracks/primary.md", "# Heading\n\nContent"))
    save_mdkv(doc, p)
    return p


def test_cli_license():
    r = CliRunner().invoke(main, ["license"])
    assert r.exit_code == 0
    assert "Apache License" in r.output




def test_cli_batch_validate_and_stats_error_paths(tmp_path: Path):
    p_good = _make_doc(tmp_path)
    p_bad = tmp_path / "corrupt.mdkv"
    p_bad.write_bytes(b"corrupt non-zip content")

    # Batch validate table format with bad file
    r1 = CliRunner().invoke(main, ["batch", "validate", str(p_good), str(p_bad)])
    assert r1.exit_code == 1
    assert "OK" in r1.output
    assert "FAIL" in r1.output

    # Batch validate json format with bad file
    r2 = CliRunner().invoke(main, ["batch", "validate", str(p_good), str(p_bad), "--json"])
    assert r2.exit_code == 1
    data = json.loads(r2.output)
    assert len(data) == 2
    assert data[0]["ok"] is True
    assert data[1]["ok"] is False

    # Batch stats with bad file
    r3 = CliRunner().invoke(main, ["batch", "stats", str(p_good), str(p_bad)])
    assert r3.exit_code == 1
    stats_data = json.loads(r3.output)
    assert len(stats_data) == 2
    assert "title" in stats_data[0]
    assert "error" in stats_data[1]


