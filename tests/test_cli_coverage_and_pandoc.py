from __future__ import annotations

"""Comprehensive tests targeting full CLI coverage (pandoc export, batch errors, license, etc.)."""

import json
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import patch

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


def test_cli_export_pandoc_success(tmp_path: Path):
    p = _make_doc(tmp_path)
    with patch("mdkv.services.pandoc_export.to_pdf", return_value=tmp_path / "doc.pdf") as mock_pdf, \
         patch("mdkv.services.pandoc_export.to_epub", return_value=tmp_path / "doc.epub") as mock_epub, \
         patch("mdkv.services.pandoc_export.to_docx", return_value=tmp_path / "doc.docx") as mock_docx:

        r1 = CliRunner().invoke(main, ["export", str(p), "--format", "pdf"])
        assert r1.exit_code == 0
        mock_pdf.assert_called_once()

        r2 = CliRunner().invoke(main, ["export", str(p), "--format", "epub"])
        assert r2.exit_code == 0
        mock_epub.assert_called_once()

        r3 = CliRunner().invoke(main, ["export", str(p), "--format", "docx"])
        assert r3.exit_code == 0
        mock_docx.assert_called_once()


def test_cli_export_pandoc_errors(tmp_path: Path):
    p = _make_doc(tmp_path)
    with patch("mdkv.services.pandoc_export.to_pdf", side_effect=FileNotFoundError("pandoc missing")):
        r1 = CliRunner().invoke(main, ["export", str(p), "--format", "pdf"])
        assert r1.exit_code != 0
        assert "pandoc missing" in r1.output

    with patch("mdkv.services.pandoc_export.to_pdf", side_effect=RuntimeError("pandoc syntax crash")):
        r2 = CliRunner().invoke(main, ["export", str(p), "--format", "pdf"])
        assert r2.exit_code != 0
        assert "pandoc conversion failed" in r2.output


def test_cli_batch_validate_and_stats_error_paths(tmp_path: Path):
    p_good = _make_doc(tmp_path)
    p_bad = tmp_path / "corrupt.mdkv"
    p_bad.write_bytes(b"corrupt non-zip content")

    # Batch validate table format with bad file
    r1 = CliRunner().invoke(main, ["batch", "validate", str(p_good), str(p_bad)])
    assert r1.exit_code == 0
    assert "OK" in r1.output
    assert "FAIL" in r1.output

    # Batch validate json format with bad file
    r2 = CliRunner().invoke(main, ["batch", "validate", str(p_good), str(p_bad), "--json"])
    assert r2.exit_code == 0
    data = json.loads(r2.output)
    assert len(data) == 2
    assert data[0]["ok"] is True
    assert data[1]["ok"] is False

    # Batch stats with bad file
    r3 = CliRunner().invoke(main, ["batch", "stats", str(p_good), str(p_bad)])
    assert r3.exit_code == 0
    stats_data = json.loads(r3.output)
    assert len(stats_data) == 2
    assert "title" in stats_data[0]
    assert "error" in stats_data[1]


def test_cli_save_incremental_full_fallback(tmp_path: Path):
    p = tmp_path / "new_nonexistent.mdkv"
    doc = MDKVDocument(title="Doc", authors=["A"], created=datetime.now(UTC))
    doc.add_track(Track("primary", "primary", "en", "tracks/primary.md", "content"))
    save_mdkv(doc, p)
    # Patch save_mdkv_incremental to return False (full fallback)
    with patch("mdkv.storage.io.save_mdkv_incremental", return_value=False):
        r = CliRunner().invoke(main, ["save-incremental", str(p)])
        assert r.exit_code == 0
        assert "Saved (full fallback)" in r.output
