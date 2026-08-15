#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
INSTALL_SYSTEM=0
INSTALL_OPTIONAL=0
INSTALL_WHISPER=0

usage() {
  cat <<'EOF'
Usage: scripts/setup_macos.sh [--install-system] [--with-optional] [--with-whisper]

Without --install-system, the script never invokes Homebrew. It creates the
Python environment, installs the package, and reports missing external tools.
--with-optional installs optional Python adapters such as faster-whisper,
PySceneDetect, and OpenTimelineIO.
--with-whisper builds the pinned whisper.cpp release and downloads the
hardware-recommended multilingual model outside the Git repository.
EOF
}

for argument in "$@"; do
  case "${argument}" in
    --install-system) INSTALL_SYSTEM=1 ;;
    --with-optional) INSTALL_OPTIONAL=1 ;;
    --with-whisper) INSTALL_WHISPER=1 ;;
    -h|--help) usage; exit 0 ;;
    *) printf 'Unknown option: %s\n' "${argument}" >&2; usage >&2; exit 2 ;;
  esac
done

if [[ "$(uname -s)" != "Darwin" ]]; then
  printf 'This setup script is for macOS.\n' >&2
  exit 2
fi

if ! command -v ffmpeg >/dev/null || ! command -v ffprobe >/dev/null; then
  if [[ "${INSTALL_SYSTEM}" -eq 1 ]]; then
    command -v brew >/dev/null || {
      printf 'Homebrew is required for --install-system. Install it first.\n' >&2
      exit 1
    }
    brew install ffmpeg
  else
    printf 'Missing FFmpeg. Re-run with --install-system or install ffmpeg manually.\n' >&2
  fi
fi

cd "${ROOT_DIR}"
if command -v uv >/dev/null; then
  if [[ "${INSTALL_OPTIONAL}" -eq 1 ]]; then
    uv sync --extra transcription --extra scene-detection --extra timeline --extra dev
  else
    uv sync --extra dev
  fi
  RUNNER=(uv run)
else
  python3 -m venv .venv
  # shellcheck disable=SC1091
  source .venv/bin/activate
  python -m pip install --upgrade pip
  if [[ "${INSTALL_OPTIONAL}" -eq 1 ]]; then
    python -m pip install -e '.[transcription,scene-detection,timeline,dev]'
  else
    python -m pip install -e '.[dev]'
  fi
  RUNNER=(python -m video_editing_th.cli)
fi

if [[ "${INSTALL_WHISPER}" -eq 1 ]]; then
  model_name="$("${RUNNER[@]}" models recommend --name-only)"
  whisper_args=(--model "${model_name}")
  if [[ "${INSTALL_SYSTEM}" -eq 1 ]]; then
    whisper_args+=(--install-system)
  fi
  "${ROOT_DIR}/scripts/setup_whisper_cpp_macos.sh" "${whisper_args[@]}"
  export PATH="${HOME}/.local/bin:${PATH}"
fi

if [[ -f "${ROOT_DIR}/skills/video-editing-th/SKILL.md" ]]; then
  "${ROOT_DIR}/scripts/install_codex_skill.sh"
fi

"${RUNNER[@]}" doctor || true
cat <<EOF

Setup finished. Local asset/footage paths are not configured automatically.
Use 'video-editing-th models recommend' and see docs/setup.md for model details.
EOF
