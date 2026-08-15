#!/usr/bin/env bash
set -euo pipefail

MODEL="auto"
INSTALL_SYSTEM=0
WHISPER_CPP_REF="${WHISPER_CPP_REF:-v1.9.2}"
WHISPER_CPP_HOME="${WHISPER_CPP_HOME:-${HOME}/.local/opt/whisper.cpp}"
MODEL_ROOT="${VIDEO_EDITING_TH_MODEL_ROOT:-${HOME}/.cache/video-editing-th/models}"
BIN_DIR="${HOME}/.local/bin"

usage() {
  cat <<'EOF'
Usage: scripts/setup_whisper_cpp_macos.sh [--model NAME] [--install-system]

Builds the pinned whisper.cpp release, links whisper-cli into ~/.local/bin,
and downloads a multilingual GGML model outside the Git repository.

Defaults:
  --model auto                  Hardware-aware model choice
  WHISPER_CPP_REF=v1.9.2        Pinned upstream release
  WHISPER_CPP_HOME=~/.local/opt/whisper.cpp
  VIDEO_EDITING_TH_MODEL_ROOT=~/.cache/video-editing-th/models

--install-system authorizes Homebrew installation of missing cmake only.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --model)
      [[ $# -ge 2 ]] || { printf '%s\n' '--model requires a value' >&2; exit 2; }
      MODEL="$2"
      shift 2
      ;;
    --install-system)
      INSTALL_SYSTEM=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      printf 'Unknown option: %s\n' "$1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

[[ "$(uname -s)" == "Darwin" ]] || {
  printf '%s\n' 'This helper is for macOS.' >&2
  exit 2
}

command -v git >/dev/null || {
  printf '%s\n' 'git is required.' >&2
  exit 1
}

if ! command -v cmake >/dev/null; then
  if [[ "${INSTALL_SYSTEM}" -eq 1 ]]; then
    command -v brew >/dev/null || {
      printf '%s\n' 'Homebrew is required to install cmake automatically.' >&2
      exit 1
    }
    brew install cmake
  else
    printf '%s\n' 'cmake is missing. Install it or re-run with --install-system.' >&2
    exit 1
  fi
fi

if [[ "${MODEL}" == "auto" ]]; then
  memory_bytes="$(sysctl -n hw.memsize 2>/dev/null || true)"
  if [[ "${memory_bytes}" =~ ^[0-9]+$ ]]; then
    memory_gib=$((memory_bytes / 1024 / 1024 / 1024))
    if (( memory_gib <= 8 )); then
      MODEL="large-v3-turbo-q5_0"
    elif (( memory_gib < 15 )); then
      MODEL="large-v3-q5_0"
    else
      MODEL="large-v3"
    fi
  else
    MODEL="large-v3-q5_0"
  fi
fi

case "${MODEL}" in
  large-v3|large-v3-q5_0|large-v3-turbo|large-v3-turbo-q5_0) ;;
  *)
    printf 'Unsupported model: %s\n' "${MODEL}" >&2
    exit 2
    ;;
esac

mkdir -p "$(dirname "${WHISPER_CPP_HOME}")" "${MODEL_ROOT}" "${BIN_DIR}"

if [[ ! -d "${WHISPER_CPP_HOME}/.git" ]]; then
  git clone --depth 1 --branch "${WHISPER_CPP_REF}" \
    https://github.com/ggml-org/whisper.cpp.git "${WHISPER_CPP_HOME}"
else
  current_ref="$(git -C "${WHISPER_CPP_HOME}" describe --tags --exact-match 2>/dev/null || true)"
  if [[ "${current_ref}" != "${WHISPER_CPP_REF}" ]]; then
    printf 'Using existing whisper.cpp checkout at %s (current ref: %s).\n' \
      "${WHISPER_CPP_HOME}" "${current_ref:-unversioned}"
    printf 'Set WHISPER_CPP_HOME to an empty location for a clean %s checkout.\n' \
      "${WHISPER_CPP_REF}"
  fi
fi

cmake -S "${WHISPER_CPP_HOME}" -B "${WHISPER_CPP_HOME}/build" -DCMAKE_BUILD_TYPE=Release
cmake --build "${WHISPER_CPP_HOME}/build" -j --config Release

WHISPER_CLI="${WHISPER_CPP_HOME}/build/bin/whisper-cli"
[[ -x "${WHISPER_CLI}" ]] || {
  printf 'whisper-cli was not produced at %s\n' "${WHISPER_CLI}" >&2
  exit 1
}
ln -sfn "${WHISPER_CLI}" "${BIN_DIR}/whisper-cli"

"${WHISPER_CPP_HOME}/models/download-ggml-model.sh" "${MODEL}" "${MODEL_ROOT}"
MODEL_PATH="${MODEL_ROOT}/ggml-${MODEL}.bin"
[[ -f "${MODEL_PATH}" ]] || {
  printf 'Expected model was not downloaded: %s\n' "${MODEL_PATH}" >&2
  exit 1
}

cat <<EOF

whisper.cpp ready.
  Upstream ref: ${WHISPER_CPP_REF}
  Binary:       ${BIN_DIR}/whisper-cli
  Model:        ${MODEL_PATH}

If ~/.local/bin is not already on PATH, add this to ~/.zshrc:
  export PATH="\$HOME/.local/bin:\$PATH"
EOF
