#!/usr/bin/env bash
# Regenerate the Word versions of the review documents.
#   cd ~/lowe && ./docs/word/build_docx.sh
# Requires: pandoc.
#
# reference.docx carries the styling (Cambria headings in deep blue, Calibri
# body, shaded code blocks with a rule, amber-tinted blockquotes). It was made
# by taking pandoc's default reference and rewriting styles.xml; regenerate it
# with `pandoc --print-default-data-file reference.docx` if it is ever lost.
#
# No --toc: pandoc emits a field that only populates when Word opens the file,
# which renders as an empty heading in any other viewer.
set -euo pipefail
cd "$(dirname "$0")/../.."

for f in CODE_REVIEW CODE_REVIEW_SCRIPT; do
  pandoc "docs/$f.md" \
    --reference-doc=docs/word/reference.docx \
    --from=gfm --to=docx --highlight-style=tango \
    -o "docs/word/$f.docx"
  echo "  docs/word/$f.docx  $(stat -c%s "docs/word/$f.docx") bytes"
done
