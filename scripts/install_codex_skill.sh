#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
SKILL_SOURCE="${ROOT_DIR}/skills/video-editing-th"
CODEX_HOME_DIR="${CODEX_HOME:-${HOME}/.codex}"
AGENTS_HOME_DIR="${AGENTS_HOME:-${HOME}/.agents}"

if [[ ! -f "${SKILL_SOURCE}/SKILL.md" ]]; then
  printf 'Skill is not present yet at %s\n' "${SKILL_SOURCE}" >&2
  exit 1
fi

link_skill() {
  local home_dir="$1"
  local destination="${home_dir}/skills/video-editing-th"
  mkdir -p "$(dirname "${destination}")"
  if [[ -L "${destination}" ]]; then
    rm "${destination}"
  elif [[ -e "${destination}" ]]; then
    printf 'Refusing to replace non-symlink path: %s\n' "${destination}" >&2
    exit 1
  fi
  ln -s "${SKILL_SOURCE}" "${destination}"
  printf 'Installed skill: %s -> %s\n' "${destination}" "${SKILL_SOURCE}"
}

link_skill "${CODEX_HOME_DIR}"
link_skill "${AGENTS_HOME_DIR}"
