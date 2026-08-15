# Thai Transcription Contract

## Source of truth

The canonical external transcript—not ChatCut's native transcript—is the source of truth for structural edits and captions. Force `language=th` wherever the backend supports it and use transcription mode, never translation mode.

Recommended local order:

1. `whisper.cpp` with a multilingual `large-v3`-class model on Apple Silicon.
2. `faster-whisper` where it is installed and benchmarked.
3. An imported, corrected canonical transcript when local ASR is not reliable enough.

Run:

```bash
video-editing-th transcribe SOURCE.mov \
  --backend auto \
  --language th \
  --output edit/transcripts/SOURCE.json
```

## Quality gate

Read the emitted quality report. Automatic structural editing requires:

```text
safe_for_automatic_editing = true
```

The validator normalizes Unicode NFC and detects the failure modes that previously corrupted Thai footage:

- wrong language routing;
- unexpected CJK characters;
- a low Thai-script ratio;
- Latin-heavy hallucinated passages;
- implausibly repeated phrases;
- text emitted in probable non-speech.

If the gate fails, keep the source untouched, preserve all uncertain speech, and obtain another transcript. Do not reinterpret repeated English/CJK output as retakes.

## Timing

Treat ASR word timestamps as candidates, not unquestionable truth. Structural edges must not land inside a word. Keep the profile's safety handles, inspect ambiguous boundaries against waveform/audio, and prefer preserving extra material over deleting a real syllable.

## Retakes

Use `video-editing-th analyze` to create `takes_packed.md` and `retake-groups.json`. Codex compares meaning, completeness, delivery, sequence, silence, and audible restarts. “Latest complete” means the most recent full usable delivery; a later false start does not replace an earlier complete take.
