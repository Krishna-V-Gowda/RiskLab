#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
export PYTHONPATH="$ROOT/src"
export PYTHONDONTWRITEBYTECODE=1
PYTHON_BIN="${PYTHON:-python3}"
WORK="${RISKLAB_VERIFY_WORK:-$(mktemp -d "${TMPDIR:-/tmp}/risklab-verify.XXXXXX")}"
if [[ -z "${RISKLAB_VERIFY_WORK:-}" ]]; then
  trap 'rm -rf "$WORK"' EXIT
fi
rm -rf "$WORK"
mkdir -p "$WORK/first" "$WORK/second"

printf '%s\n' '[1/6] unit, numerical, temporal-integrity and reduced E2E tests'
"$PYTHON_BIN" -m unittest discover -s tests -v

printf '%s\n' '[2/6] source compilation without bytecode residue'
"$PYTHON_BIN" - "$ROOT" <<'PY'
from pathlib import Path
import sys
root=Path(sys.argv[1])
paths=sorted((root/'src').rglob('*.py'))+sorted((root/'tests').rglob('*.py'))+sorted((root/'scripts').rglob('*.py'))
for path in paths:
    compile(path.read_text(encoding='utf-8'), str(path), 'exec')
print(f'compiled {len(paths)} Python files')
PY

printf '%s\n' '[3/6] reduced end-to-end run twice'
"$PYTHON_BIN" -m risklab.cli run --output-dir "$WORK/first" --days 300 --assets 5 --bootstrap-resamples 30 --scenario-limit 1 >/dev/null
"$PYTHON_BIN" -m risklab.cli run --output-dir "$WORK/second" --days 300 --assets 5 --bootstrap-resamples 30 --scenario-limit 1 >/dev/null

printf '%s\n' '[4/6] semantic determinism check'
"$PYTHON_BIN" - "$WORK/first/results.json" "$WORK/second/results.json" <<'PY'
import json, sys
from pathlib import Path

def load(path):
    value=json.loads(Path(path).read_text())
    value.pop('runtime_seconds',None)
    value.pop('environment',None)
    return value
if load(sys.argv[1]) != load(sys.argv[2]):
    raise SystemExit('semantic outputs differ')
print('semantic outputs are identical')
PY

printf '%s\n' '[5/6] first-party credential and private-key scan'
"$PYTHON_BIN" - "$ROOT" <<'PY'
import re, sys
from pathlib import Path
root=Path(sys.argv[1])
patterns=[
 re.compile(r'AKIA[0-9A-Z]{16}'),
 re.compile(r'gh[pousr]_[A-Za-z0-9_]{30,}'),
 re.compile(r'AIza[0-9A-Za-z_-]{30,}'),
 re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),
]
excluded={'.git','.verification','.publisher-venv','.venv','venv','__pycache__','build','dist','node_modules','.next'}
for path in root.rglob('*'):
    if not path.is_file() or any(part in excluded for part in path.parts):
        continue
    if path.resolve() == Path(__file__).resolve() if '__file__' in globals() else False:
        continue
    if path == root/'scripts'/'verify.sh' or path.stat().st_size>5_000_000:
        continue
    try: text=path.read_text(encoding='utf-8')
    except (UnicodeDecodeError,OSError): continue
    for pattern in patterns:
        if pattern.search(text):
            raise SystemExit(f'credential-like material in {path.relative_to(root)}')
print('no credential patterns detected')
PY

printf '%s\n' '[6/6] source-tree residue guard'
if find "$ROOT" -type d \( -name __pycache__ -o -name .pytest_cache -o -name .verification -o -name .publisher-venv -o -name .venv -o -name node_modules -o -name .next -o -name build -o -name dist \) -print -quit | grep -q .; then
  echo 'generated residue detected in source tree' >&2
  exit 1
fi
printf '%s\n' 'RiskLab verification passed.'
