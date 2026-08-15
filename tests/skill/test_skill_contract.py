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


def test_skill_declares_complete_default_mission_and_project_overrides() -> None:
    text = read(SKILL)
    lowered = text.casefold()

    for phrase in [
        "unless the user overrides",
        "fast-paced vertical",
        "1080x1920",
        "30 fps",
        "remove mistakes",
        "latest complete",
        "b-roll",
        "overlays",
        "chatcut-native sound effects",
        "chatcut-native music",
        "chatcut-native transitions",
        "punch-ins",
        "render",
        "repair",
    ]:
        assert phrase in lowered
    assert "$video-editing-th <footage-folder>" in text
    assert "per-project override" in lowered


def test_skill_makes_captions_an_explicit_per_project_choice() -> None:
    text = read(SKILL).casefold()

    assert "only add captions when the current prompt explicitly requests them" in text
    assert "if the prompt is silent about captions, omit them" in text
    assert "caption preference" not in text


def test_skill_references_every_operational_guide_and_core_command() -> None:
    text = read(SKILL)
    expected_references = [
        "references/configuration.md",
        "references/thai-transcription.md",
        "references/asr-models.md",
        "references/asset-selection.md",
        "references/chatcut-execution.md",
        "references/qa.md",
    ]
    for reference in expected_references:
        assert reference in text
        assert (SKILL_ROOT / reference).is_file()

    for command in [
        "video-editing-th configure",
        "video-editing-th config show",
        "video-editing-th doctor",
        "video-editing-th models recommend",
        "video-editing-th project init",
        "video-editing-th transcribe",
        "video-editing-th analyze",
        "video-editing-th assets index-configured",
        "video-editing-th assets search",
        "video-editing-th plan validate",
        "video-editing-th chatcut export",
    ]:
        assert command in text


def test_reference_contracts_cover_configuration_execution_and_bounded_qa() -> None:
    configuration = read(SKILL_ROOT / "references" / "configuration.md")
    chatcut = read(SKILL_ROOT / "references" / "chatcut-execution.md")
    assets = read(SKILL_ROOT / "references" / "asset-selection.md")
    thai = read(SKILL_ROOT / "references" / "thai-transcription.md")
    asr = read(SKILL_ROOT / "references" / "asr-models.md")
    qa = read(SKILL_ROOT / "references" / "qa.md")

    assert "one-time" in configuration.casefold()
    assert "never invent" in configuration.casefold()
    assert "B-roll folder" in configuration
    assert "Overlay/graphics folder" in configuration
    assert "Backgrounds folder" in configuration
    for removed in [
        "Sound-effects folder",
        "Music folder",
        "Transitions folder",
        "output width",
        "output height",
        "whether Thai captions are enabled",
    ]:
        assert removed not in configuration
    assert "config show" in configuration
    assert "MCP" in chatcut
    assert "browser" in chatcut.casefold()
    assert "structural" in chatcut.casefold()
    assert "ChatCut AI" in chatcut
    assert "native sound" in chatcut.casefold()
    assert "native music" in chatcut.casefold()
    assert "native transition" in chatcut.casefold()
    assert "shortlist" in assets.casefold()
    assert "contact sheet" in assets.casefold()
    assert "visual verification" in assets.casefold()
    assert "local visual" in assets.casefold()
    assert "language" in thai.casefold() and "th" in thai
    assert "CJK" in thai
    assert "safe_for_automatic_editing" in thai
    assert "8 GB" in asr
    assert "large-v3-turbo-q5_0" in asr
    assert "speech recognition" in asr.casefold()
    assert "three" in qa.casefold() or "3" in qa
    assert "cut boundar" in qa.casefold()


def test_skill_has_pressure_scenarios_and_no_placeholders() -> None:
    scenario_files = sorted((ROOT / "tests" / "skill" / "scenarios").glob("*.md"))
    assert len(scenario_files) >= 5
    combined = "\n".join(read(path) for path in scenario_files)
    for marker in [
        "corrupted Thai",
        "latest complete",
        "asset shortlist",
        "browser fallback",
        "first-use configuration",
    ]:
        assert marker in combined

    deployed_text = "\n".join(
        read(path) for path in [SKILL, *sorted((SKILL_ROOT / "references").glob("*.md"))]
    )
    assert "TODO" not in deployed_text
    assert "TBD" not in deployed_text
