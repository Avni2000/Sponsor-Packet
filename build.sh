#!/usr/bin/env bash
# Render sponsor-doc.html to output/sponsor-doc.pdf and output/sponsor-doc-<page>.png

# Uses Chrome to print to pdf
set -euo pipefail
cd "$(dirname "$0")"

CHROME=$(command -v google-chrome || command -v chromium || command -v chromium-browser || true)
[ -n "$CHROME" ] || { echo "Need Chrome/Chromium"; exit 1; }
command -v pdftoppm >/dev/null || { echo "Need pdftoppm (apt install poppler-utils)"; exit 1; }

mkdir -p output
"$CHROME" --headless --disable-gpu --no-pdf-header-footer \
  --print-to-pdf=output/sponsor-doc.pdf "file://$PWD/sponsor-doc.html"
pdftoppm -png -r 150 output/sponsor-doc.pdf output/sponsor-doc
echo "Wrote:"; ls output
