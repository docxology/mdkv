from click.testing import CliRunner

from mdkv.cli import main


def test_cli_has_gui_command_help():
    r = CliRunner().invoke(main, ["--help"])
    assert r.exit_code == 0
    assert "gui" in r.output


