from __future__ import annotations

"""Targeted tests for i18n Spanish, French, English, and CLI output integration."""

from datetime import UTC, datetime
from pathlib import Path

from click.testing import CliRunner

from mdkv.cli import main
from mdkv.core.model import MDKVDocument, Track
from mdkv.i18n import _, set_language
from mdkv.storage import save_mdkv


def test_i18n_translation_catalogs():
    # Spanish
    set_language("es")
    assert _("Title") == "Título"
    assert _("Authors") == "Autores"
    assert _("Version") == "Versión"
    assert _("Tracks") == "Pistas"
    assert _("Created") == "Creado"
    assert _("No differences found.") == "No se encontraron diferencias."

    # French
    set_language("fr")
    assert _("Title") == "Titre"
    assert _("Authors") == "Auteurs"
    assert _("Version") == "Version"
    assert _("Tracks") == "Pistes"
    assert _("Created") == "Créé"
    assert _("No differences found.") == "Aucune différence trouvée."

    # English fallback / reset
    set_language("en")
    assert _("Title") == "Title"
    assert _("Authors") == "Authors"
    assert _("No differences found.") == "No differences found."


def test_cli_i18n_integration(tmp_path: Path):
    p1 = tmp_path / "doc1.mdkv"
    p2 = tmp_path / "doc2.mdkv"
    doc1 = MDKVDocument(title="Doc", authors=["A"], created=datetime.now(UTC))
    doc1.add_track(Track("primary", "primary", "en", "tracks/primary.md", "content"))
    save_mdkv(doc1, p1)
    save_mdkv(doc1, p2)

    # CLI diff in Spanish
    set_language("es")
    r_diff_es = CliRunner().invoke(main, ["diff", str(p1), str(p2)])
    assert r_diff_es.exit_code == 0
    assert "No se encontraron diferencias." in r_diff_es.output

    # CLI info in Spanish table format
    r_info_es = CliRunner().invoke(main, ["info", str(p1), "--format", "table"])
    assert r_info_es.exit_code == 0
    assert "Título:" in r_info_es.output
    assert "Autores:" in r_info_es.output

    # CLI diff in French
    set_language("fr")
    r_diff_fr = CliRunner().invoke(main, ["diff", str(p1), str(p2)])
    assert r_diff_fr.exit_code == 0
    assert "Aucune différence trouvée." in r_diff_fr.output

    # Reset language
    set_language("en")
