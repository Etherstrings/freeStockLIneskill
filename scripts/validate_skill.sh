#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "${ROOT_DIR}"

test -f freestocklineskill/SKILL.md
test -f freestocklineskill/agents/openai.yaml
test -x freestocklineskill/scripts/stockline_cli.py

python3 -m py_compile freestocklineskill/scripts/stockline_cli.py freestocklineskill/scripts/runtime/freestocklineskill_runtime/*.py
python3 -m pytest -q

python3 freestocklineskill/scripts/stockline_cli.py endpoint-list >/dev/null
python3 freestocklineskill/scripts/stockline_cli.py search-entity --query "贵州茅台" >/dev/null

printf 'Validation ok\n'
