from datetime import datetime
from pathlib import Path

from mdkv.core.model import MDKVDocument, Track
from mdkv.services.export import to_markdown, to_html, export_to_files


def test_export_functions_covering_branches(tmp_path: Path):
    d = MDKVDocument(title="T", authors=["A"], created=datetime(2025, 1, 1))
    d.add_track(Track("p", "primary", "en", "tracks/p.md", "# P"))
    d.add_track(Track("n", "commentary", None, "tracks/n.md", "Note"))
    # include filter branch
    md = to_markdown(d, include_track_types=["commentary"])  # noqa: F841
    # html branch
    html = to_html(d)  # noqa: F841
    # export_to_files branch
    export_to_files(d, tmp_path, include_track_types=["primary"])  # writes p.md
    assert (tmp_path / "p.md").exists()


