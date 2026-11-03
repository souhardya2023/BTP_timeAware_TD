"""N4d: a CNN on the git history as a time-series image: the last 12 releases x 7 channels (event, log interest lines, log changed lines, project activity,
share of the project's instances active, same-file neighbour events, exists) + static size / age.  1-D convolutions over time.
Real and synthetic histories; held-out projects (5 folds) and temporal (first 60 % of each project's releases train).  AUC and capture in the top 20 / 30 % against persistence + size ties.
Run with the torch Python."""
import numpy as np, pandas as pd, torch, torch.nn as nn, time
from sload import boot_ci, capture
torch.set_num_threads(2)
def auc(y, p):
    r = pd.Series(p).rank().values; n1 = y.sum(); n0 = len(y) - n1
    return (r[y == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0)
class Net(nn.Module):
    def __init__(s, cin=7, st=4):
        super().__init__()
        s.c = nn.Sequential(nn.Conv1d(cin, 32, 3, padding=1), nn.ReLU(), nn.Conv1d(32, 32, 3, padding=1), nn.ReLU())
        s.h = nn.Sequential(nn.Linear(64 + st, 64), nn.ReLU(), nn.Dropout(0.2), nn.Linear(64, 1))
    def forward(s, x, z):
        h = s.c(x.transpose(1, 2)); return s.h(torch.cat([h.mean(2), h.amax(2), z], 1)).squeeze(1)
def fit_predict(Xtr, Ztr, ytr, Xte, Zte, seed, epochs=14):
    torch.manual_seed(seed); m = Net(); opt = torch.optim.Adam(m.parameters(), 2e-3)
    Xt, Zt, yt = map(torch.tensor, (Xtr, Ztr, ytr.astype(np.float32)))
    for ep in range(epochs):
        m.train(); perm = torch.randperm(len(yt))
        for i in range(0, len(yt), 256):
            b = perm[i:i + 256]; loss = nn.functional.binary_cross_entropy_with_logits(m(Xt[b], Zt[b]), yt[b]); opt.zero_grad(); loss.backward(); opt.step()
    m.eval()
    with torch.no_grad():
        return torch.sigmoid(m(torch.tensor(Xte), torch.tensor(Zte))).numpy()
out = []
P = lambda s="": (out.append(s), print(s, flush=True))
for name in ("real", "synthetic"):
    D = pd.read_csv("../results/n4_rows_%s.csv" % name).fillna(0); X = np.load("../results/n4_seq_%s.npy" % name)
    if name == "synthetic": keep = (D.regime == "baseline").values | True
    Z = np.stack([np.log1p(D.nloc0), D.ccn0 / 20, D.age / 20, np.log1p(D.principal_pm * 1000)], 1).astype(np.float32)
    y = D.ev.values; D["persist"] = D.past_il / (D.age + 1) + 1e-9 * D.nloc0
    for proto in ("held-out projects", "temporal"):
        p = np.zeros(len(D)); test = np.ones(len(D), bool)
        if proto == "temporal":
            cut = D.groupby("repo").vi.transform(lambda s: s.quantile(0.6)).values
            tr, te = np.where(D.vi.values <= cut)[0], np.where(D.vi.values > cut)[0]
            p[te] = np.mean([fit_predict(X[tr], Z[tr], y[tr], X[te], Z[te], s) for s in (0, 1)], 0); test = np.zeros(len(D), bool); test[te] = True
        else:
            repos = np.array(D.repo.unique().tolist()); rng = np.random.default_rng(0); rng.shuffle(repos); f = {r: i % 5 for i, r in enumerate(repos)}; fo = D.repo.map(f).values; assert len(set(repos)) == D.repo.nunique() and not pd.isna(fo).any()
            for k in range(5):
                te = np.where(fo == k)[0]; tr = np.where(fo != k)[0]
                p[te] = np.mean([fit_predict(X[tr], Z[tr], y[tr], X[te], Z[te], s) for s in (0, 1)], 0)
        T = D[test].assign(p=p[test])
        res = {"cnn": {0.2: [], 0.3: []}, "persist": {0.2: [], 0.3: []}}
        for (repo, vi), g in T.groupby(["repo", "vi"]):
            if len(g) < (10 if name == "real" else 6) or g.y.sum() <= 0: continue
            for q in (0.2, 0.3):
                res["cnn"][q].append(np.mean([capture(g.p.values + 1e-9 * g.nloc0.values, g.y.values, q, np.random.default_rng(t)) for t in range(3)]))
                res["persist"][q].append(np.mean([capture(g.persist.values, g.y.values, q, np.random.default_rng(t)) for t in range(3)]))
        line = "%-9s %-18s AUC cnn %.3f persistence %.3f" % (name, proto, auc(T.ev.values, T.p.values), auc(T.ev.values, T.persist.values))
        for q in (0.2, 0.3):
            d = (np.array(res["cnn"][q]) - np.array(res["persist"][q])) * 100
            line += " | top %d%%: persistence %.1f, cnn %+.1f (%+.1f, %+.1f) [%d groups]" % (q * 100, np.mean(res["persist"][q]) * 100, d.mean(), *boot_ci(d), len(d))
        P(line)
open("../results/n4d_seq_cnn.txt", "w").write("\n".join(out))
