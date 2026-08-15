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
    "docs/configuration.md",
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
        "docs/configuration.md",
        "docs/asset-library.md",
        "docs/chatcut.md",
        "docs/troubleshooting.md",
        "SECURITY.md",
    ]:
        assert link in readme

    for phrase in [
        "video-editing-th configure",
        "video-editing-th config show",
        "video-editing-th assets index-configured",
        "$video-editing-th <footage-folder>",
        "ChatCut-native sound effects",
        "ChatCut-native music",
        "ChatCut-native transitions",
        "captions are a per-project prompt choice",
        "1080x1920 at 30 fps",
    ]:
        assert phrase in readme


def test_configuration_docs_do_not_request_native_chatcut_or_output_choices() -> None:
    combined = "\n".join(
        (ROOT / relative).read_text(encoding="utf-8")
        for relative in [
            "README.md",
            "docs/setup.md",
            "docs/configuration.md",
            "docs/asset-library.md",
        ]
    )
    for removed in [
        "Sound-effects folder",
        "Music folder",
        "Transitions folder",
        "--sfx",
        "--music",
        "--transitions",
        "--width 1080",
        "--height 1920",
        "--fps 30",
        "--captions",
        "captions_enabled",
    ]:
        assert removed not in combined


def test_documented_help_commands_execute() -> None:
    commands = [
        ["--help"],
        ["configure", "--help"],
        ["config", "path", "--help"],
        ["config", "show", "--help"],
        ["doctor", "--help"],
        ["project", "init", "--help"],
        ["project", "inventory", "--help"],
        ["transcribe", "--help"],
        ["analyze", "--help"],
        ["assets", "index", "--help"],
        ["assets", "index-configured", "--help"],
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


def test_setup_scripts_route_uv_through_the_project_cli() -> None:
    for relative in ["scripts/setup_macos.sh", "scripts/setup_debian.sh"]:
        script = (ROOT / relative).read_text(encoding="utf-8")
        assert "RUNNER=(uv run video-editing-th)" in script
        assert '"${RUNNER[@]}" doctor' in script


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
