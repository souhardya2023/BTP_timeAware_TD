#!/usr/bin/env bash
# Bare clones (full history) of the additional real projects. The 10 original projects are already in ../../../repos.
# usage: a0_clone_corpus.sh [DEST]   (default ../../../repos)
DEST="${1:-$(dirname "$0")/../../../repos}"
mkdir -p "$DEST"
while read -r name url; do
  [ -d "$DEST/$name.git" ] && { echo "$name: exists"; continue; }
  timeout 900 git clone --bare --quiet "$url" "$DEST/$name.git" 2>/dev/null && echo "$name: $(git -C "$DEST/$name.git" rev-list --count HEAD) commits" || { echo "$name: FAILED"; rm -rf "$DEST/$name.git"; }
done <<'LIST'
requests https://github.com/psf/requests
flask https://github.com/pallets/flask
attrs https://github.com/python-attrs/attrs
rich https://github.com/Textualize/rich
httpx https://github.com/encode/httpx
tqdm https://github.com/tqdm/tqdm
pyyaml https://github.com/yaml/pyyaml
more-itertools https://github.com/more-itertools/more-itertools
cachetools https://github.com/tkem/cachetools
bottle https://github.com/bottlepy/bottle
jsonschema https://github.com/python-jsonschema/jsonschema
arrow https://github.com/arrow-py/arrow
lz4 https://github.com/lz4/lz4
libuv https://github.com/libuv/libuv
hiredis https://github.com/redis/hiredis
jemalloc https://github.com/jemalloc/jemalloc
libsodium https://github.com/jedisct1/libsodium
lua https://github.com/lua/lua
tmux https://github.com/tmux/tmux
cmark https://github.com/commonmark/cmark
redis https://github.com/redis/redis
zstd https://github.com/facebook/zstd
libxml2 https://github.com/GNOME/libxml2
mbedtls https://github.com/Mbed-TLS/mbedtls
LIST
