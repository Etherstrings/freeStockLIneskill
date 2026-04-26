#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SOURCE_DIR="${ROOT_DIR}/freestocklineskill"
TARGET_DIR="${OPENCLAW_SKILL_DIR:-$HOME/.openclaw/workspace/skills/freestocklineskill}"

if [[ ! -d "${SOURCE_DIR}" ]]; then
  echo "Missing skill folder: ${SOURCE_DIR}" >&2
  exit 1
fi

mkdir -p "$(dirname "${TARGET_DIR}")"
rm -rf "${TARGET_DIR}"
cp -R "${SOURCE_DIR}" "${TARGET_DIR}"
chmod +x "${TARGET_DIR}/scripts/stockline_cli.py" || true

printf 'Installed freeStockLIneskill to %s\n' "${TARGET_DIR}"
