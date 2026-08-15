#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
INSTALL_SYSTEM=0
INSTALL_OPTIONAL=0

usage() {
  cat <<'EOF'
Usage: scripts/setup_debian.sh [--install-system] [--with-optional]

Without --install-system, the script does not run apt or sudo. It creates the
Python environment, installs the package, and reports missing external tools.
EOF
}

for argument in "$@"; do
  case "${argument}" in
    --install-system) INSTALL_SYSTEM=1 ;;
    --with-optional) INSTALL_OPTIONAL=1 ;;
    -h|--help) usage; exit 0 ;;
    *) printf 'Unknown option: %s\n' "${argument}" >&2; usage >&2; exit 2 ;;
  esac
done

if [[ ! -f /etc/debian_version ]]; then
  printf 'This setup script targets Debian/Ubuntu systems.\n' >&2
  exit 2
fi

if ! command -v ffmpeg >/dev/null || ! command -v ffprobe >/dev/null; then
  if [[ "${INSTALL_SYSTEM}" -eq 1 ]]; then
    sudo apt-get update
    sudo apt-get install -y ffmpeg python3-venv git
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

if [[ -f "${ROOT_DIR}/skills/video-editing-th/SKILL.md" ]]; then
  "${ROOT_DIR}/scripts/install_codex_skill.sh"
fi

"${RUNNER[@]}" doctor || true
printf '\nSetup finished. Configure local model, footage, and asset paths manually.\n'
