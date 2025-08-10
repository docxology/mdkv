#!/usr/bin/env bash
set -euo pipefail

# Build the paper publication bundle using the Python helper (requires project env)
# Usage examples:
#   ./build_paper_bundle.sh --out paper.mdkv --bundle-dir _bundle
#   ./build_paper_bundle.sh --no-clone
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Ensure uv is available and in PATH
if ! command -v uv >/dev/null 2>&1; then
  echo "Installing uv (not found on PATH)" >&2
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.local/bin:$PATH"
fi

uv run python3 "$SCRIPT_DIR/build_paper_bundle.py" "$@"


