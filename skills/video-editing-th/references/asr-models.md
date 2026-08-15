# Local ASR Model Selection

Use local whisper.cpp for Thai speech recognition when available. The ASR model produces Thai text, timing, and confidence evidence; it does **not** make editorial or creative decisions.

## Machine check

Run:

```bash
video-editing-th models recommend
video-editing-th models list
video-editing-th doctor
```

On an **8 GB Apple Silicon Mac**, use `large-v3-turbo-q5_0` for normal throughput and `large-v3-q5_0` when accuracy matters more than speed. Full `large-v3` can run, but do not prefer it while Codex, browser automation, ChatCut, and FFmpeg are competing for unified memory.

On machines with roughly 16 GB RAM or more, full `large-v3` is the default accuracy baseline.

## Operational rule

Before transcription, verify that the recommended GGML model is present in the configured model cache. If the normal recommended model is missing, install it rather than silently switching to an unrelated or English-only model.

Never use a model ending in `.en` for Thai.

Transcribe explicitly as Thai:

```bash
video-editing-th transcribe <clip> --backend whisper.cpp --language th
```

When the recommended cached model exists, the CLI can resolve it without an explicit `--model` path. Override the model only for a deliberate benchmark or accuracy comparison.

## Quality over speed

The Thai quality gate remains authoritative. If a faster or quantized model produces CJK leakage, repeated hallucinations, low Thai-script ratios, or otherwise fails `safe_for_automatic_editing`, preserve the footage and retry with the accuracy model before making cuts.
