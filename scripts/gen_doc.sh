#!/bin/bash

# Move to the tools directory, no matter where it is launched from
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.." || exit 1

echo "Generating commands documentation..."
pydoc-markdown -I src/pypixelcolor/commands > wiki/Commands.md