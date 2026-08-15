from __future__ import annotations

import tomllib
from pathlib import Path

from typer.testing import CliRunner

from video_editing_th.cli import app

ROOT = Path(__file__).resolve().parents[1]
runner = CliRunner()


REQUIRED_DOCS = [
    "README.md",
    "docs/architecture.md",
    "docs/setup.md",
    "docs/project-layout.md",
    "docs/asset-library.md",
    "docs/chatcut.md",
    "docs/troubleshooting.md",
    "docs/upstream.md",
    "THIRD_PARTY.md",
    "NOTICE",
    "LICENSE",
    "CONTRIBUTING.md",
    "SECURITY.md",
    ".github/workflows/ci.yml",
    ".github/ISSUE_TEMPLATE/bug_report.yml",
    ".github/pull_request_template.md",
]


def test_required_release_documents_exist_and_are_linked() -> None:
    for relative in REQUIRED_DOCS:
        assert (ROOT / relative).is_file(), relative

    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    for link in [
        "docs/architecture.md",
        "docs/setup.md",
        "docs/asset-library.md",
        "docs/chatcut.md",
        "docs/troubleshooting.md",
        "SECURITY.md",
    ]:
        assert link in readme


def test_documented_help_commands_execute() -> None:
    commands = [
        ["--help"],
        ["doctor", "--help"],
        ["project", "init", "--help"],
        ["project", "inventory", "--help"],
        ["transcribe", "--help"],
        ["analyze", "--help"],
        ["assets", "index", "--help"],
        ["assets", "search", "--help"],
        ["plan", "validate", "--help"],
        ["captions", "build", "--help"],
        ["render", "preview", "--help"],
        ["chatcut", "export", "--help"],
        ["skill", "install", "--help"],
    ]
    for command in commands:
        result = runner.invoke(app, command)
        assert result.exit_code == 0, f"{command}: {result.stdout}"


def test_upstream_attribution_and_no_placeholders() -> None:
    notice = (ROOT / "NOTICE").read_text(encoding="utf-8")
    third_party = (ROOT / "THIRD_PARTY.md").read_text(encoding="utf-8")
    assert "browser-use/video-use" in notice
    assert "92c2b34e44c205cbc2acae7f6ca7c1c219d5dd66" in notice
    assert "Copyright (c) 2026 Browser Use" in third_party
    assert "MIT License" in third_party

    deployed = "\n".join(
        path.read_text(encoding="utf-8")
        for path in [
            ROOT / "README.md",
            *sorted((ROOT / "docs").glob("*.md")),
            ROOT / "CONTRIBUTING.md",
            ROOT / "SECURITY.md",
        ]
    )
    assert "TODO" not in deployed
    assert "TBD" not in deployed
    assert "/mnt/data" not in deployed


def test_package_metadata_includes_skill_and_profile_data() -> None:
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    data_files = pyproject["tool"]["setuptools"]["data-files"]

    assert "share/video-editing-th/skill" in data_files
    assert "share/video-editing-th/skill/references" in data_files
    assert "share/video-editing-th/profiles" in data_files
    assert pyproject["project"]["requires-python"] == ">=3.11"


def test_ci_enforces_lint_types_tests_build_and_shell_checks() -> None:
    ci = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    for version in ["3.11", "3.12", "3.13"]:
        assert version in ci
    for command in [
        "ruff check",
        "ruff format --check",
        "mypy",
        "pytest",
        "python -m build",
        "bash -n",
    ]:
        assert command in ci
