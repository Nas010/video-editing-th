from typer.testing import CliRunner

from video_editing_th.cli import app


runner = CliRunner()


def test_root_help_lists_primary_workflows() -> None:
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "Thai talking-head" in result.stdout
    assert "doctor" in result.stdout
    assert "project" in result.stdout
    assert "assets" in result.stdout
    assert "plan" in result.stdout
