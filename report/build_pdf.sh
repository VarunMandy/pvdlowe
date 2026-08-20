#!/usr/bin/env bash
# Regenerate the technical report as a styled A4 PDF.
#   cd ~/lowe && ./report/build_pdf.sh
# Requires: python3-markdown, wkhtmltopdf, poppler-utils (for QA).
set -euo pipefail
cd "$(dirname "$0")"

python3 - <<'PY'
import markdown, pathlib, re
md = pathlib.Path('TECHNICAL_REPORT.md').read_text()
html = markdown.markdown(md, extensions=['tables','fenced_code','sane_lists','toc','attr_list'])
# the metadata block under the H1 loses its line breaks in markdown; restore them
def fix(m):
    parts = [x.strip() for x in
             re.split(r'(?<=\S)\s+(?=<strong>|Framework:)', m.group(1)) if x.strip()]
    return '<p class="meta">' + '<br>'.join(parts) + '</p>' if len(parts) > 1 else m.group(0)
html = re.sub(r'(?<=</h1>)\s*<p>(.*?)</p>', fix, html, count=1, flags=re.S)
pathlib.Path('TECHNICAL_REPORT.html').write_text(
    '<!DOCTYPE html><html><head><meta charset="utf-8">'
    '<link rel="stylesheet" href="style.css"></head><body>' + html + '</body></html>')
PY

wkhtmltopdf --enable-local-file-access --page-size A4 \
  --margin-top 16mm --margin-bottom 18mm --margin-left 16mm --margin-right 16mm \
  --footer-html footer.html --footer-spacing 5 \
  --enable-internal-links --outline --outline-depth 3 \
  TECHNICAL_REPORT.html TECHNICAL_REPORT.pdf

pdfinfo TECHNICAL_REPORT.pdf | grep -E 'Pages|Page size'
echo "written $(pwd)/TECHNICAL_REPORT.pdf"
