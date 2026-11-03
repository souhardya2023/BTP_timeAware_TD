"""N1: code -> image.  The changed lines of a debt introduction (git diff of parent -> child) are drawn as an image:
 rows = changed lines (first the file of the debt, up to 64 lines), columns = characters (first 96), 
 channel 0 = character class (letter, digit, underscore, quote, bracket, operator, punctuation, space/indent ...) scaled to 0..1
 channel 1 = +1 for an added line, -1 for a removed line
Synthetic pairs: from the git repositories; real pairs (61): from td.patch.   Output: results/n1_images.npz"""
import os, re, subprocess, sys
import numpy as np
import pandas as pd
from sload import SD, ROOT

H, W = 64, 96
CLS = {}
for c in "abcdefghijklmnopqrstuvwxyz": CLS[c] = 1
for c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ": CLS[c] = 2
for c in "0123456789": CLS[c] = 3
CLS["_"] = 4
for c in "\"'": CLS[c] = 5
for c in "()": CLS[c] = 6
for c in "[]": CLS[c] = 7
for c in "{}": CLS[c] = 8
for c in "=<>!": CLS[c] = 9
for c in "+-*/%&|^~": CLS[c] = 10
for c in ".,": CLS[c] = 11
for c in ":;": CLS[c] = 12
for c in "#@$\\?": CLS[c] = 13
CLS[" "] = 14
CLS["\t"] = 14
NC = 15.0

def to_image(lines):
    img = np.zeros((2, H, W), np.float32)
    for r, (sign, text) in enumerate(lines[:H]):
        img[1, r, :] = sign
        for c, ch in enumerate(text[:W]):
            img[0, r, c] = CLS.get(ch, 15) / NC
    return img

def parse_diff(text, first_file=None):
    files, cur = {}, None
    for l in text.splitlines():
        if l.startswith("diff --git"):
            m = re.search(r" b/(\S+)$", l); cur = m.group(1) if m else l
            files.setdefault(cur, [])
        elif l.startswith(("+++", "---", "@@", "index", "new file", "deleted file", "similarity", "rename")):
            continue
        elif cur is not None and l[:1] in "+-" and l[1:].strip():
            files[cur].append((1.0 if l[0] == "+" else -1.0, l[1:].rstrip()))
    order = sorted(files, key=lambda f: (f != first_file, f))
    return [x for f in order for x in files[f]]

if __name__ == "__main__":
    P = pd.read_csv(os.path.join(SD, "pairs.csv"))
    I = pd.read_csv(os.path.join(SD, "instances.csv")).set_index("instance")
    F = pd.read_csv(os.path.join(SD, "features", "pairs_delta.csv"))[["instance"]]
    P = F.merge(P, on="instance")
    X, meta = [], []
    for _, r in P.iterrows():
        t = subprocess.run(["git", "-C", os.path.join(SD, "repos", r.project + ".git"), "diff", "-U0", r.parent, r.child], capture_output=True, text=True).stdout
        X.append(to_image(parse_diff(t, I.loc[r.instance].file)))
        meta.append((r.instance, r.project, r.ptype, r.template, r.tier, r.regime, bool(r.mixed), r.intro_release))
    X = np.array(X)
    M = pd.DataFrame(meta, columns=["instance", "project", "ptype", "template", "tier", "regime", "mixed", "intro_release"])
    # real pairs
    PR = pd.read_csv(os.path.join(ROOT, "project_dataset", "properties_all_pairs.csv")).set_index("id")
    DS = pd.read_csv(os.path.join(ROOT, "out_dataset", "delta_only", "dataset_without_time.csv"))
    XR, mr = [], []
    for pid, ty, lang, proj in zip(DS.id, DS.td_type, DS.language, DS.project):
        l, n = pid.split("/")
        patch = os.path.join(ROOT, "project_dataset", "Python" if l == "Python" else "C_C++", n, n + "_prop", "td.patch")
        XR.append(to_image(parse_diff(open(patch, errors="ignore").read())))
        mr.append((pid, proj, ty, lang))
    np.savez_compressed("../results/n1_images.npz", X=X, XR=np.array(XR))
    M.to_csv("../results/n1_meta.csv", index=False)
    pd.DataFrame(mr, columns=["id", "project", "ptype", "language"]).to_csv("../results/n1_meta_real.csv", index=False)
    print("synthetic images", X.shape, "real images", np.array(XR).shape, "mean rows used", float((np.abs(X[:, 1]).sum(2) > 0).sum(1).mean()))
