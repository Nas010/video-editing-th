from pathlib import Path

from video_editing_th.asr_models import (
    HardwareProfile,
    model_path,
    recommend_whisper_model,
    resolve_model_name,
)


def test_m1_8gb_defaults_to_turbo_quantized_model() -> None:
    hardware = HardwareProfile(os_name="Darwin", architecture="arm64", memory_gib=8.0)

    recommendation = recommend_whisper_model(hardware)

    assert recommendation.default_model == "large-v3-turbo-q5_0"
    assert recommendation.accuracy_model == "large-v3-q5_0"
    assert recommendation.full_large_v3_supported is True
    assert recommendation.full_large_v3_recommended is False


def test_16gb_apple_silicon_can_default_to_full_large_v3() -> None:
    hardware = HardwareProfile(os_name="Darwin", architecture="arm64", memory_gib=16.0)

    recommendation = recommend_whisper_model(hardware)

    assert recommendation.default_model == "large-v3"
    assert recommendation.full_large_v3_recommended is True


def test_auto_model_resolves_from_hardware() -> None:
    hardware = HardwareProfile(os_name="Darwin", architecture="arm64", memory_gib=8.0)

    assert resolve_model_name("auto", hardware) == "large-v3-turbo-q5_0"
    assert resolve_model_name("large-v3-q5_0", hardware) == "large-v3-q5_0"


def test_model_path_uses_expected_whisper_cpp_filename(tmp_path: Path) -> None:
    assert model_path(tmp_path, "large-v3-q5_0") == tmp_path / "ggml-large-v3-q5_0.bin"
