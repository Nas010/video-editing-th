from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SKILL_ROOT = ROOT / "skills" / "video-editing-th"
SKILL = SKILL_ROOT / "SKILL.md"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_skill_has_discoverable_frontmatter() -> None:
    text = read(SKILL)

    assert text.startswith("---\n")
    assert "name: video-editing-th" in text
    assert "description: Use when" in text
    assert "Thai talking-head" in text.split("---", 2)[1]


def test_skill_enforces_quality_gate_and_codex_decision_ownership() -> None:
    text = read(SKILL)

    assert "quality gate" in text.casefold()
    assert "Codex makes" in text
    assert "Never delegate" in text
    assert "ChatCut AI" in text
    assert "preserve" in text.casefold()


def test_skill_references_every_operational_guide_and_core_command() -> None:
    text = read(SKILL)
    expected_references = [
        "references/thai-transcription.md",
        "references/asset-selection.md",
        "references/chatcut-execution.md",
        "references/qa.md",
    ]
    for reference in expected_references:
        assert reference in text
        assert (SKILL_ROOT / reference).is_file()

    for command in [
        "video-editing-th doctor",
        "video-editing-th project init",
        "video-editing-th transcribe",
        "video-editing-th analyze",
        "video-editing-th assets search",
        "video-editing-th plan validate",
        "video-editing-th chatcut export",
    ]:
        assert command in text


def test_reference_contracts_cover_execution_and_bounded_qa() -> None:
    chatcut = read(SKILL_ROOT / "references" / "chatcut-execution.md")
    assets = read(SKILL_ROOT / "references" / "asset-selection.md")
    thai = read(SKILL_ROOT / "references" / "thai-transcription.md")
    qa = read(SKILL_ROOT / "references" / "qa.md")

    assert "MCP" in chatcut
    assert "browser" in chatcut.casefold()
    assert "structural" in chatcut.casefold()
    assert "ChatCut AI" in chatcut
    assert "shortlist" in assets.casefold()
    assert "contact sheet" in assets.casefold()
    assert "visual verification" in assets.casefold()
    assert "language" in thai.casefold() and "th" in thai
    assert "CJK" in thai
    assert "safe_for_automatic_editing" in thai
    assert "three" in qa.casefold() or "3" in qa
    assert "cut boundar" in qa.casefold()


def test_skill_has_pressure_scenarios_and_no_placeholders() -> None:
    scenario_files = sorted((ROOT / "tests" / "skill" / "scenarios").glob("*.md"))
    assert len(scenario_files) >= 4
    combined = "\n".join(read(path) for path in scenario_files)
    for marker in ["corrupted Thai", "latest complete", "asset shortlist", "browser fallback"]:
        assert marker in combined

    deployed_text = "\n".join(
        read(path) for path in [SKILL, *sorted((SKILL_ROOT / "references").glob("*.md"))]
    )
    assert "TODO" not in deployed_text
    assert "TBD" not in deployed_text
