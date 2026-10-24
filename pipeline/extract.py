"""Vector of ONE project: its structural features and its technical-debt features (nothing else).

  s_*  structure   directory layout and module/#include dependency graph (46)
  c_*  code        size and shape of the code: lines, per-function size/complexity, language idioms (50)
  t_*  td          technical debt: smells and their principal, SATD comments, duplication, security, concurrency, cohesion (37)

`extract(folder)` -> {feature name: value}   (133 named, human-readable numbers; counts are log-scaled or per-KLOC, ratios are 0..1)
"""
import os
import sys
import warnings

warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import dominant_lang, src_files
from f_code import analyze, code_features
from f_structure import structure
from f_td import td_features


def extract(root, lang=None):
    files = src_files(root)
    if not files:
        raise ValueError(f"no source files (.py .c .h .cc .cpp) found under {root}")
    lang = lang or dominant_lang(files)
    ctx = analyze(root, files)
    s, _wl, _g = structure(root, files, lang)
    feats = {}
    feats.update(s)
    feats.update(code_features(ctx))
    feats.update(td_features(root, ctx, lang))
    return feats


if __name__ == "__main__":
    f = extract(sys.argv[1])
    for k, v in f.items():
        print(f"{k:36s} {v:.4f}")
    print(len(f), "features")
