#!/usr/bin/env bash
set -euo pipefail

# Build the paper publication bundle using the Python helper (requires project env)
# Usage examples:
#   ./build_paper_bundle.sh --out paper.mdkv --bundle-dir _bundle
#   ./build_paper_bundle.sh --no-clone
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Provision explicitly with the repository's uv sync --extra dev workflow.
# Never download a host installer as a side effect of rendering a manuscript.
if ! command -v uv >/dev/null 2>&1; then
  echo "uv is required; install it explicitly before building this repository." >&2
  exit 1
fi

uv run --no-sync --project "$SCRIPT_DIR/.." python "$SCRIPT_DIR/build_paper_bundle.py" "$@"


