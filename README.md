# video-editing-th

[![CI](https://github.com/Nas010/video-editing-th/actions/workflows/ci.yml/badge.svg)](https://github.com/Nas010/video-editing-th/actions/workflows/ci.yml)

A Codex-driven production pipeline for turning raw Thai talking-head footage into a reviewable edit. Local tools handle transcription, Thai Unicode validation, waveform/silence evidence, retake candidates, reusable-asset search, captions, plan validation, and a rough preview. Codex makes the editorial decisions and operates ChatCut through MCP/browser controls to build the editable final timeline.

## What it covers

- explicit Thai (`th`) transcription through `whisper.cpp`, optional `faster-whisper`, or imported corrected JSON;
- hard rejection of CJK leakage, repeated hallucinations, wrong-language routing, and low Thai-script ratios;
- conservative retake grouping with “latest complete take” evidence;
- word-safe structural cuts, pause tightening, and output-time Thai captions;
- persistent SQLite catalog for B-roll, overlays, transitions, images, music, and SFX;
- contact sheets and shortlist retrieval so Codex does not repeatedly inspect every asset;
- versioned edit plans with B-roll, overlays, zoom/pan/reframe, SFX, and transitions;
- deterministic FFmpeg rough previews;
- ordered ChatCut execution manifests for Codex-controlled MCP/browser editing;
- bounded render QA and portable Codex skill installation.

ChatCut AI is not used. ChatCut is the NLE; Codex is the editor.

## Architecture

```text
raw footage ─┬─> ffprobe / waveform / silence ─┐
             └─> Thai ASR + quality gate ──────┤
                                                v
                                      Codex edit reasoning
asset folders ─> SQLite catalog ─> shortlist ──┤
                                                v
                                     versioned EditPlan
                                       ├─> FFmpeg preview
                                       └─> ChatCut manifest
                                                v
                                  Codex controls ChatCut NLE
                                                v
                                    editable project + render
```

The canonical plan, transcript, quality report, and asset database remain independent of ChatCut. See [the architecture](docs/architecture.md).

## Quick start

### macOS

```bash
git clone https://github.com/Nas010/video-editing-th.git
cd video-editing-th
scripts/setup_macos.sh
```

Add `--install-system` only when the script should install missing FFmpeg through Homebrew. Add `--with-optional` to install the optional Python ASR/scene/timeline adapters.

### Debian or Ubuntu

```bash
git clone https://github.com/Nas010/video-editing-th.git
cd video-editing-th
scripts/setup_debian.sh
```

The setup scripts do not download model weights, upload footage, or configure personal folders. Complete those local choices using [the setup guide](docs/setup.md).

## Core workflow

```bash
# Verify the machine without changing it.
video-editing-th doctor

# Create project output under FOOTAGE/edit/ and inventory source media.
video-editing-th project init FOOTAGE --profile profiles/thai-fast-reel.yaml
video-editing-th project inventory FOOTAGE

# Transcribe each source with an explicit Thai route.
video-editing-th transcribe FOOTAGE/clip.mov \
  --backend whisper.cpp \
  --model /path/to/ggml-large-v3.bin \
  --language th \
  --output FOOTAGE/edit/transcripts/clip.json

# Produce compact evidence for Codex's retake decisions.
video-editing-th analyze FOOTAGE/edit/transcripts/clip.json \
  --profile profiles/thai-fast-reel.yaml \
  --output-dir FOOTAGE/edit/analysis/clip

# Validate the plan, map captions, and render a local review cut.
video-editing-th plan validate FOOTAGE/edit/plans/edit-plan.json \
  --transcripts FOOTAGE/edit/transcripts \
  --profile profiles/thai-fast-reel.yaml
video-editing-th captions build FOOTAGE/edit/plans/edit-plan.json \
  --transcripts FOOTAGE/edit/transcripts \
  --profile profiles/thai-fast-reel.yaml \
  --output FOOTAGE/edit/plans/edit-plan-captioned.json \
  --srt-output FOOTAGE/edit/captions.srt
video-editing-th render preview FOOTAGE/edit/plans/edit-plan-captioned.json \
  --output FOOTAGE/edit/renders/rough-preview.mp4 \
  --burn-captions

# Give Codex deterministic operations to execute in ChatCut.
video-editing-th chatcut export FOOTAGE/edit/plans/edit-plan-captioned.json \
  --output FOOTAGE/edit/plans/chatcut.json
```

The Codex skill is installed by the setup script or directly:

```bash
video-editing-th skill install
```

## Reusable creative assets

```bash
video-editing-th assets index /path/to/assets \
  --catalog /path/to/assets/.video-editing-th/catalog.db \
  --preview-dir /path/to/assets/.video-editing-th/previews

video-editing-th assets search "เวทเทรนนิ่ง กล้ามเนื้ออก" \
  --catalog /path/to/assets/.video-editing-th/catalog.db \
  --role broll \
  --orientation portrait
```

Descriptions, tags, use cases, contact sheets, and file hashes persist between projects. Read [the asset-library guide](docs/asset-library.md).

## Production boundaries

- The first release targets chronological single-speaker Thai talking-head footage.
- Low-confidence or semantically unclear speech is preserved and marked for review.
- Model accuracy depends on recording quality and the chosen multilingual ASR weights.
- The local preview renders structural cuts and captions; ChatCut is responsible for the editable creative pass.
- Codex must have access to the ChatCut MCP integration and browser controls to execute the NLE manifest.
- Calibration against several raw/manual-edit pairs is strongly recommended before unattended use.

## Documentation

- [Architecture](docs/architecture.md)
- [Setup](docs/setup.md)
- [Project layout](docs/project-layout.md)
- [Asset library](docs/asset-library.md)
- [ChatCut execution](docs/chatcut.md)
- [Troubleshooting](docs/troubleshooting.md)
- [Upstream relationship](docs/upstream.md)
- [Security policy](SECURITY.md)
- [Contributing](CONTRIBUTING.md)

## License and origin

This repository is MIT licensed. It is a substantial derivative and architectural specialization of [`browser-use/video-use`](https://github.com/browser-use/video-use); attribution and the retained upstream license are in [NOTICE](NOTICE) and [THIRD_PARTY.md](THIRD_PARTY.md).
