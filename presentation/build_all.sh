#!/bin/bash
# Rebuild everything: figures, table images, then the deck (run twice so table sizes are known).
cd "$(dirname "$0")"
python3 make_figures.py
python3 make_architecture.py
node build_deck_final.js      # writes tables_spec.json
python3 make_tables.py        # draws tables/*.png
node build_deck_final.js      # places the images
