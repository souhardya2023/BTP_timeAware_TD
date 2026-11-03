"""L1-B3: a small CNN on the 32x32 dependency-graph images (channel 1: debt copy, channel 2: debt minus clean), 5 types.
Run with a Python that has torch (the miniforge python of this machine).  Seeds 0..4; stratified folds of the dataset and leave-one-project-out."""
import numpy as np
import pandas as pd
import torch
import torch.nn as nn

D = np.load("../results/l1_images.npz", allow_pickle=True)
td, dl, y, proj, fold = D["td"], D["delta"], D["y"], D["proj"], D["fold"]
classes = sorted(set(y)); yi = np.array([classes.index(t) for t in y])
def norm(a):
    return np.sign(a) * np.log1p(np.abs(a))
X = np.stack([norm(td), norm(dl)], 1).astype(np.float32)

def net():
    return nn.Sequential(nn.Conv2d(2, 8, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2), nn.Conv2d(8, 16, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2),
                         nn.AdaptiveAvgPool2d(2), nn.Flatten(), nn.Dropout(0.3), nn.Linear(64, len(classes)))

def fit_predict(tr, te, seed):
    torch.manual_seed(seed)
    m = net(); opt = torch.optim.AdamW(m.parameters(), 3e-3, weight_decay=1e-2)
    w = torch.tensor(1.0 / np.bincount(yi[tr], minlength=len(classes)).clip(1), dtype=torch.float32); w = w / w.mean()
    xt, yt = torch.tensor(X[tr]), torch.tensor(yi[tr])
    for ep in range(150):
        m.train(); perm = torch.randperm(len(tr))
        for i in range(0, len(tr), 16):
            b = perm[i:i + 16]
            loss = nn.functional.cross_entropy(m(xt[b]), yt[b], weight=w)
            opt.zero_grad(); loss.backward(); opt.step()
    m.eval()
    with torch.no_grad():
        return m(torch.tensor(X[te])).argmax(1).numpy()

res = {}
for split in ("stratified", "leave_one_project_out"):
    folds = fold if split == "stratified" else pd.factorize(proj)[0]
    accs = []
    for seed in range(5):
        pred = np.zeros(len(y), int)
        for f in np.unique(folds):
            te = np.where(folds == f)[0]; tr = np.where(folds != f)[0]
            pred[te] = fit_predict(tr, te, seed)
        accs.append((pred == yi).mean())
    res[split] = (np.mean(accs), np.std(accs))
    print(f"CNN {split}: accuracy {np.mean(accs):.3f} +- {np.std(accs):.3f} over 5 seeds (majority {np.bincount(yi).max()/len(yi):.3f})")
open("../results/l1_cnn.txt", "w").write("\n".join(f"CNN {k}: accuracy {v[0]:.3f} +- {v[1]:.3f} over 5 seeds; majority 0.426" for k, v in res.items()))
