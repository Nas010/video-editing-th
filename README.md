# video-editing-th

[![CI](https://github.com/Nas010/video-editing-th/actions/workflows/ci.yml/badge.svg)](https://github.com/Nas010/video-editing-th/actions/workflows/ci.yml)

A Codex-driven production pipeline for turning raw Thai talking-head footage into a polished vertical Reel. Local tools handle Thai transcription, quality validation, waveform/silence evidence, retake candidates, reusable visual-asset search, optional captions, plan validation, and rough previews. Codex makes the editorial and creative decisions and operates ChatCut through MCP/browser controls to build the editable final timeline.

ChatCut AI is not used. ChatCut is the NLE; Codex is the editor.

## Default result

Once the one-time machine configuration is complete, the normal invocation is:

```text
$video-editing-th <footage-folder>
```

Unless the user overrides a setting for that project, the skill produces a fast-paced **1080x1920 at 30 fps** Thai Reel: mistakes, false starts, superseded retakes, and excess dead air are removed; the latest complete good takes are selected; relevant local B-roll, overlays, and backgrounds are retrieved from the configured visual library; restrained motion effects are added; and Codex selects appropriate **ChatCut-native sound effects**, **ChatCut-native music**, and **ChatCut-native transitions** inside the editor. The editable timeline is built in ChatCut, rendered, inspected, and repaired through a bounded QA loop.

**Captions are a per-project prompt choice.** Ask for Thai captions in the current prompt when they are wanted. If the prompt is silent about captions, the skill omits them.

## What it covers

- explicit Thai (`th`) transcription through `whisper.cpp`, optional `faster-whisper`, or imported corrected JSON;
- hardware-aware local Whisper model selection, including an 8 GB Apple Silicon profile;
- hard rejection of CJK leakage, repeated hallucinations, wrong-language routing, and low Thai-script ratios;
- conservative retake grouping with “latest complete take” evidence;
- word-safe structural cuts and pause tightening;
- optional output-time Thai captions generated only when requested for the current project;
- one-time per-machine configuration for local B-roll, overlay/graphics, and background folders;
- persistent SQLite catalog and contact sheets for local visual assets;
- native ChatCut references for sound effects, music, and transitions without pretending they are local files;
- versioned edit plans with B-roll, overlays, zoom/pan/reframe, native audio, and transitions;
- deterministic FFmpeg rough previews;
- ordered ChatCut execution manifests for Codex-controlled MCP/browser editing;
- bounded render QA and portable Codex skill installation.

## Architecture

```text
raw footage ─┬─> ffprobe / waveform / silence ─┐
             └─> Thai ASR + quality gate ──────┤
                                                v
                                      Codex edit reasoning
local visual assets -> SQLite catalog -> shortlist
                                                v
                                     versioned EditPlan
                                       ├─> FFmpeg preview
                                       └─> ChatCut manifest
                                                v
                 ChatCut native SFX/music/transitions + Codex control
                                                v
                                 editable project + render + QA
```

The canonical plan, transcript, quality report, and local visual-asset database remain independent of ChatCut. See [the architecture](docs/architecture.md).

## Install

### macOS with local Thai ASR

```bash
git clone https://github.com/Nas010/video-editing-th.git
cd video-editing-th
scripts/setup_macos.sh --install-system --with-whisper
```

This installs the project/Codex skill, builds a pinned whisper.cpp release, and downloads a model chosen from the machine's RAM. On a 2020 M1 MacBook Air with 8 GB RAM, the normal default is `large-v3-turbo-q5_0`; `large-v3-q5_0` is the accuracy-oriented option. See [Local Thai ASR Models](docs/asr-models.md).

Add `--with-optional` to install the optional Python ASR/scene/timeline adapters as well.

### Debian or Ubuntu

```bash
git clone https://github.com/Nas010/video-editing-th.git
cd video-editing-th
scripts/setup_debian.sh
```

The setup scripts do not upload footage or invent personal paths. Complete the local visual-library choices through the one-time wizard.

## One-time machine configuration

Run:

```bash
video-editing-th configure
```

The wizard asks only for optional local B-roll, overlay/graphics, and background folders plus the default editing profile. It does not ask about ChatCut's native media, social-video dimensions, frame rate, or captions. The resulting YAML lives outside Git.

Inspect it:

```bash
video-editing-th config path
video-editing-th config show --json
```

Index all configured local visual folders together:

```bash
video-editing-th assets index-configured
```

Read [the configuration guide](docs/configuration.md) for interactive and Codex-assisted non-interactive setup.

## Check the local ASR setup

```bash
video-editing-th models recommend
video-editing-th models list
video-editing-th doctor
```

Whisper is the speech-recognition stage: it produces Thai text, timing, and confidence evidence. It does not edit the video. Codex combines the transcript with waveform/silence evidence to choose retakes and cuts. When captions are requested, the validated transcript also supplies their text and timing.

When the recommended model exists in the normal cache, an explicit model path is optional:

```bash
video-editing-th transcribe FOOTAGE/clip.mov \
  --backend whisper.cpp \
  --language th
```

## Pipeline commands

Codex normally orchestrates these through the installed skill, but each stage remains directly reproducible:

```bash
video-editing-th doctor

video-editing-th project init FOOTAGE \
  --profile profiles/thai-fast-reel.yaml
video-editing-th project inventory FOOTAGE

video-editing-th transcribe FOOTAGE/clip.mov \
  --backend whisper.cpp \
  --language th \
  --output FOOTAGE/edit/transcripts/clip.json

video-editing-th analyze FOOTAGE/edit/transcripts/clip.json \
  --profile profiles/thai-fast-reel.yaml \
  --output-dir FOOTAGE/edit/analysis/clip

video-editing-th plan validate FOOTAGE/edit/plans/edit-plan.json \
  --transcripts FOOTAGE/edit/transcripts \
  --profile profiles/thai-fast-reel.yaml

# Run this caption stage only when the current project prompt requested captions.
video-editing-th captions build FOOTAGE/edit/plans/edit-plan.json \
  --transcripts FOOTAGE/edit/transcripts \
  --profile profiles/thai-fast-reel.yaml \
  --output FOOTAGE/edit/plans/edit-plan-captioned.json \
  --srt-output FOOTAGE/edit/captions.srt

video-editing-th render preview FOOTAGE/edit/plans/edit-plan.json \
  --output FOOTAGE/edit/renders/rough-preview.mp4

video-editing-th chatcut export FOOTAGE/edit/plans/edit-plan.json \
  --output FOOTAGE/edit/plans/chatcut.json
```

`chatcut export` defaults to 1080x1920 at 30 fps. Explicit format flags remain available only for a project that genuinely needs another format.

The Codex skill is installed by the setup script or directly:

```bash
video-editing-th skill install
```

## Local visual assets

After `video-editing-th assets index-configured`, search and annotation commands use the configured catalog automatically:

```bash
video-editing-th assets search "เวทเทรนนิ่ง กล้ามเนื้ออก" \
  --role broll \
  --orientation portrait
```

Descriptions, tags, use cases, contact sheets, and file hashes persist between projects. Search returns a shortlist; Codex visually verifies finalists before placement. Sound effects, music, and transitions are selected from ChatCut's native libraries during the creative pass. Read [the asset-library guide](docs/asset-library.md).

## Prompt examples

Without captions:

```text
$video-editing-th /Users/name/Footage/Reel-04
```

With Thai captions:

```text
$video-editing-th /Users/name/Footage/Reel-04 — add Thai captions
```

Project-specific instructions override only what they mention, for example “use less B-roll” or “make this landscape.”

## Production boundaries

- The first release targets chronological single-speaker Thai talking-head footage.
- Low-confidence or semantically unclear speech is preserved and marked for review.
- Model accuracy depends on recording quality and the chosen multilingual ASR weights.
- The local preview renders structural cuts and any requested captions; ChatCut is responsible for the editable creative pass.
- Codex must have access to the ChatCut MCP integration and browser controls to execute the NLE manifest.
- Calibration against several raw/manual-edit pairs is strongly recommended before unattended use.

## Documentation

- [Architecture](docs/architecture.md)
- [Setup](docs/setup.md)
- [One-time configuration](docs/configuration.md)
- [Local Thai ASR models](docs/asr-models.md)
- [Project layout](docs/project-layout.md)
- [Asset library](docs/asset-library.md)
- [ChatCut execution](docs/chatcut.md)
- [Troubleshooting](docs/troubleshooting.md)
- [Upstream relationship](docs/upstream.md)
- [Security policy](SECURITY.md)
- [Contributing](CONTRIBUTING.md)

## License and origin

This repository is MIT licensed. It is a substantial derivative and architectural specialization of [`browser-use/video-use`](https://github.com/browser-use/video-use); attribution and the retained upstream license are in [NOTICE](NOTICE) and [THIRD_PARTY.md](THIRD_PARTY.md).
