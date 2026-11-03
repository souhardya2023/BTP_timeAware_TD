#!/usr/bin/env bash
# Clone the 10 repositories of the study as bare clones (full history) into the folder given as argument (default: ../../repos).
# Their git history is the input of the interest calculation. About 95 MB; needs network access.
set -e
DEST="${1:-$(dirname "$0")/../../../repos}"
mkdir -p "$DEST"
while read -r name url; do
  [ -d "$DEST/$name.git" ] || git clone --bare --quiet "$url" "$DEST/$name.git"
  echo "$name: $(git -C "$DEST/$name.git" rev-list --count HEAD) commits"
done <<'LIST'
boltons https://github.com/mahmoud/boltons
click https://github.com/pallets/click
jinja https://github.com/pallets/jinja
werkzeug https://github.com/pallets/werkzeug
C-Thread-Pool https://github.com/Pithikos/C-Thread-Pool
cJSON https://github.com/DaveGamble/cJSON
jansson https://github.com/akheron/jansson
libpng https://github.com/pnggroup/libpng
libyaml https://github.com/yaml/libyaml
zlib https://github.com/madler/zlib
LIST
echo "note: the study used the state of these repositories on 2026-10-08; later commits and releases change the numbers slightly (use --k and --window as documented)."
