#!/usr/bin/env bash
# Rebuild the report from refactor-kit/runs: figures + generated tables/numbers, then the PDF.
# Usage: ./build.sh            (PYTHON=/path/to/python ./build.sh to use another interpreter with matplotlib)
set -euo pipefail
cd "$(dirname "$0")"
PY="${PYTHON:-$HOME/tools/hw2-venv/bin/python}"
"$PY" make_report.py
for _ in 1 2; do pdflatex -interaction=nonstopmode -halt-on-error report.tex >/dev/null; done
if grep -nE "Overfull|Undefined value|undefined references|Citation.*undefined" report.log; then
  echo "WARNING: see the lines above in report.log"
fi
echo "built $(pwd)/report.pdf ($(pdfinfo report.pdf 2>/dev/null | awk '/^Pages/{print $2}') pages)"
