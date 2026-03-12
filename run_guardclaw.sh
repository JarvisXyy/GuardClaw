#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   ./run_guardclaw.sh [OPENCLAW_ROOT] [SKILL_FILE] [LOCK_LEVEL]
# Example:
#   ./run_guardclaw.sh
#   ./run_guardclaw.sh /path/to/openclaw
#   ./run_guardclaw.sh /path/to/openclaw ./docs/SKILL.md strict

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${SCRIPT_DIR}"
OPENCLAW_ROOT="${1:-${SCRIPT_DIR}}"
SKILL_FILE="${2:-${PROJECT_ROOT}/docs/SKILL.md}"
LOCK_LEVEL="${3:-soft}"
VENV_PATH="${OPENCLAW_ROOT}/.venv"

if [[ ! -d "${OPENCLAW_ROOT}" ]]; then
  echo "Error: OPENCLAW_ROOT not found: ${OPENCLAW_ROOT}"
  exit 1
fi

if [[ ! -f "${SKILL_FILE}" ]]; then
  echo "Error: SKILL file not found: ${SKILL_FILE}"
  exit 1
fi

if [[ "${LOCK_LEVEL}" != "off" && "${LOCK_LEVEL}" != "soft" && "${LOCK_LEVEL}" != "strict" ]]; then
  echo "Error: LOCK_LEVEL must be one of: off, soft, strict"
  exit 1
fi

if [[ ! -d "${VENV_PATH}" ]]; then
  python3 -m venv "${VENV_PATH}"
fi

# shellcheck source=/dev/null
source "${VENV_PATH}/bin/activate"

python3 -m pip install -U pip
python3 -m pip install -e "${PROJECT_ROOT}"

guardclaw --root "${OPENCLAW_ROOT}" all --skill-file "${SKILL_FILE}" --lock-level "${LOCK_LEVEL}"
