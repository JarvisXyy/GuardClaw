#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   ./run_guardclaw.sh <OPENCLAW_ROOT> [SKILL_FILE]

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <OPENCLAW_ROOT> [SKILL_FILE]"
  exit 1
fi

OPENCLAW_ROOT="$1"
SKILL_FILE="${2:-/Users/jarvis_xyy/Desktop/SKILL.md}"
PROJECT_ROOT="/Users/jarvis_xyy/Documents/Playground"
VENV_PATH="${OPENCLAW_ROOT}/.venv"

if [[ ! -d "${OPENCLAW_ROOT}" ]]; then
  echo "Error: OPENCLAW_ROOT not found: ${OPENCLAW_ROOT}"
  exit 1
fi

if [[ ! -f "${SKILL_FILE}" ]]; then
  echo "Error: SKILL file not found: ${SKILL_FILE}"
  exit 1
fi

if [[ ! -d "${VENV_PATH}" ]]; then
  python3 -m venv "${VENV_PATH}"
fi

# shellcheck source=/dev/null
source "${VENV_PATH}/bin/activate"

python3 -m pip install -U pip
python3 -m pip install -e "${PROJECT_ROOT}"

guardclaw --root "${OPENCLAW_ROOT}" all --skill-file "${SKILL_FILE}"
