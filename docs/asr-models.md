# Local Thai ASR Models

## What the Whisper model is used for

Whisper is the **speech-recognition layer**, not the video editor.

For every raw talking-head clip the pipeline uses the local ASR model to produce:

- Thai transcript text;
- speech segment timestamps;
- token/word timing evidence where available;
- confidence/probability signals used by quality checks;
- the text source for optional Thai captions.

Codex combines that transcript with waveform/silence evidence to identify retakes, false starts, mistakes, and safe cut boundaries. Codex still decides what to keep. ChatCut still executes the editable timeline. Whisper does **not** choose B-roll, zooms, overlays, SFX, or creative edits.

```text
raw video
  -> FFmpeg extracts 16 kHz mono audio
  -> whisper.cpp transcribes explicitly as Thai (th)
  -> Thai Unicode / hallucination quality gate
  -> transcript + timings + waveform
  -> Codex edit decisions
  -> validated EditPlan
  -> ChatCut execution
```

## 2020 M1 MacBook Air with 8 GB RAM

Yes, whisper.cpp runs on this machine. Apple Silicon is a first-class whisper.cpp target and its Metal backend runs inference on the Apple GPU.

The important constraint is **unified memory**. The official whisper.cpp documentation lists the unquantized `large` family at about **3.9 GB runtime memory** and 2.9 GiB on disk. On an 8 GB Mac, that leaves limited headroom for macOS, Codex, a browser, ChatCut, and video processing at the same time.

Therefore this project uses these defaults:

| Machine class | Normal default | Accuracy mode | Full `large-v3` |
| --- | --- | --- | --- |
| <= 8.5 GiB RAM | `large-v3-turbo-q5_0` | `large-v3-q5_0` | Runnable, but not recommended as the normal concurrent-editing model |
| > 8.5 and < 15 GiB | `large-v3-q5_0` | `large-v3-q5_0` | Supported, but leave headroom for the editor |
| >= 15 GiB | `large-v3` | `large-v3` | Recommended accuracy baseline |

For an 8 GB M1 Air, start with **`large-v3-turbo-q5_0`** for production throughput. Benchmark **`large-v3-q5_0`** on the same Thai clips when transcription quality matters more than speed. Use full `large-v3` as an occasional reference benchmark rather than keeping it loaded while the rest of the editing stack is active.

The recommendation is intentionally conservative; real speed and memory pressure depend on clip length, macOS version, thermal conditions, and what else is open.

## Model sizes

The supported multilingual whisper.cpp artifacts are:

| Model | Approx. disk size | Intended use here |
| --- | ---: | --- |
| `large-v3` | 2.9 GiB | maximum-quality reference / >=16 GB default |
| `large-v3-q5_0` | 1.1 GiB | accuracy mode on constrained machines |
| `large-v3-turbo` | 1.5 GiB | faster unquantized alternative |
| `large-v3-turbo-q5_0` | 547 MiB | 8 GB production default |

All four are multilingual. Do not use a model name ending in `.en` for Thai.

Upstream sources:

- `ggml-org/whisper.cpp` README: Apple Silicon/Metal support and documented memory usage;
- `ggml-org/whisper.cpp/models/README.md`: model artifact sizes and multilingual/quantized naming.

## Check the recommendation

```bash
video-editing-th models recommend
```

For scripts:

```bash
video-editing-th models recommend --name-only
```

List cached models:

```bash
video-editing-th models list
```

## One-command macOS setup

From a cloned repository:

```bash
scripts/setup_macos.sh --install-system --with-whisper
```

This keeps external assets outside Git and performs the following:

1. installs FFmpeg and CMake through Homebrew only when they are missing and `--install-system` was explicitly supplied;
2. installs the Python package and Codex skill;
3. clones the pinned whisper.cpp release into `~/.local/opt/whisper.cpp`;
4. builds `whisper-cli`;
5. links it at `~/.local/bin/whisper-cli`;
6. detects RAM and downloads the recommended model to `~/.cache/video-editing-th/models`;
7. runs `video-editing-th doctor`.

The repository currently pins whisper.cpp `v1.9.2` for reproducibility. Override `WHISPER_CPP_REF` deliberately when validating a newer upstream release.

## Manual setup

To install only whisper.cpp and its model:

```bash
bash scripts/setup_whisper_cpp_macos.sh --model auto --install-system
```

Or force the accuracy-oriented quantized model:

```bash
bash scripts/setup_whisper_cpp_macos.sh --model large-v3-q5_0 --install-system
```

Model weights are intentionally excluded from Git.

## Transcription

After installation, the recommended cached model is discovered automatically when `--model` is omitted:

```bash
video-editing-th transcribe /path/to/clip.mov \
  --backend whisper.cpp \
  --language th
```

You can still override it explicitly:

```bash
video-editing-th transcribe /path/to/clip.mov \
  --backend whisper.cpp \
  --model ~/.cache/video-editing-th/models/ggml-large-v3-q5_0.bin \
  --language th
```

The pipeline converts source media to the 16-bit, 16 kHz mono WAV input expected by `whisper-cli`; you do not need to convert your `.mov` files manually.
