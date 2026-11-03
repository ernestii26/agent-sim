#!/bin/bash
# Build docs/<name>.md into a pptx and render every slide to PNG for checking.
#
#   tools/build_deck.sh study5-criteria [render_dir]
#
# Works in the deck working copy outside the repo (PPT_DIR, default /tmp2/b12902056/ppt):
# copies the .md and docs/figs/ in, runs pandoc, shrinks table text (pandoc cannot set it:
# 12pt, 11pt for tables of 14+ data rows), copies the pptx back to docs/, and renders
# slides to <render_dir>/slide-NN.png. Read the PNGs before calling the deck done.
set -e
name=$1; [ -n "$name" ] || { echo "usage: $0 <deck name> [render_dir]" >&2; exit 2; }
ROOT=$(cd "$(dirname "$0")/.." && pwd)
PPT=${PPT_DIR:-/tmp2/b12902056/ppt}
OUT=${2:-$(mktemp -d)}
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT

\cp -f "$ROOT/docs/$name.md" "$PPT/"
[ -d "$ROOT/docs/figs" ] && mkdir -p "$PPT/figs" && \cp -f "$ROOT"/docs/figs/* "$PPT/figs/"
(cd "$PPT" && pandoc "$name.md" -t pptx --slide-level=1 -o "$name.pptx")

(cd "$WORK" && unzip -q "$PPT/$name.pptx" 'ppt/slides/*' && python3 - <<'PY'
import glob, re
def shrink(m):
    g = m.group(0)
    sz = "1100" if g.count("<a:tr ") >= 15 else "1200"
    return g.replace("<a:rPr />", f'<a:rPr sz="{sz}" />').replace('<a:rPr b="1" />', f'<a:rPr sz="{sz}" b="1" />')
for p in glob.glob("ppt/slides/slide*.xml"):
    s = open(p).read()
    t = re.sub(r"<a:tbl>.*?</a:tbl>", shrink, s, flags=re.S)
    if t != s:
        open(p, "w").write(t)
PY
zip -q "$PPT/$name.pptx" ppt/slides/*.xml)

\cp -f "$PPT/$name.pptx" "$ROOT/docs/"
libreoffice --headless --convert-to pdf --outdir "$WORK" "$PPT/$name.pptx" >/dev/null 2>&1
mkdir -p "$OUT" && pdftoppm -png -r 60 "$WORK/$name.pdf" "$OUT/slide"
echo "built docs/$name.pptx; slides rendered to $OUT"
