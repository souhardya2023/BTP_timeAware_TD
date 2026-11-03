"""N2: a CNN on the code images of the debt changes.  Same splits as the feature models (random, held-out project, held-out template) and
a sim-to-real test: train on all synthetic pairs, predict the 61 real pairs (Python 41, C/C++ 20).  Run with the torch Python."""
import numpy as np, pandas as pd, torch, torch.nn as nn, time
torch.set_num_threads(2)
D = np.load("../results/n1_images.npz"); X, XR = D["X"], D["XR"]
M = pd.read_csv("../results/n1_meta.csv"); MR = pd.read_csv("../results/n1_meta_real.csv")
classes = sorted(M.ptype.unique()); ci = {c: i for i, c in enumerate(classes)}
y = M.ptype.map(ci).values; yR = MR.ptype.map(ci).values
rng0 = np.random.default_rng(0)

def net():
    def blk(i, o): return nn.Sequential(nn.Conv2d(i, o, 3, padding=1), nn.BatchNorm2d(o), nn.ReLU(), nn.MaxPool2d(2))
    class N(nn.Module):
        def __init__(s):
            super().__init__(); s.f = nn.Sequential(blk(2, 16), blk(16, 32), blk(32, 64)); s.h = nn.Sequential(nn.Dropout(0.3), nn.Linear(128, len(classes)))
        def forward(s, x):
            z = s.f(x); return s.h(torch.cat([z.mean((2, 3)), z.amax((2, 3))], 1))
    return N()

def fit_predict(tr, Xte, seed, epochs=30):
    torch.manual_seed(seed); m = net(); opt = torch.optim.AdamW(m.parameters(), 2e-3, weight_decay=1e-3)
    w = torch.tensor(1.0 / np.bincount(y[tr], minlength=len(classes)).clip(1), dtype=torch.float32); w = w / w.mean()
    xt, yt = torch.tensor(X[tr]), torch.tensor(y[tr])
    for ep in range(epochs):
        m.train(); perm = torch.randperm(len(tr))
        for i in range(0, len(tr), 64):
            b = perm[i:i + 64]
            loss = nn.functional.cross_entropy(m(xt[b]), yt[b], weight=w); opt.zero_grad(); loss.backward(); opt.step()
    m.eval()
    with torch.no_grad():
        return torch.softmax(m(torch.tensor(Xte)), 1).numpy()

def folds(kind):
    f = np.zeros(len(y), int)
    if kind == "random":
        for c in range(len(classes)):
            idx = rng0.permutation(np.where(y == c)[0]); f[idx] = np.arange(len(idx)) % 5
    elif kind == "project":
        order = M.project.value_counts().index.tolist(); load = np.zeros(5)
        assign = {}
        for p in order:
            k = int(load.argmin()); assign[p] = k; load[k] += (M.project == p).sum()
        f = M.project.map(assign).values
    else:
        for c in range(len(classes)):
            ts = M[M.ptype == classes[c]].template.unique(); ts = rng0.permutation(ts)
            for j, t in enumerate(ts):
                f[(M.template == t).values] = j % 5
    return f
res, t0 = [], time.time()
for kind in ("random", "project", "template"):
    f = folds(kind); accs = []
    for seed in (0, 1):
        pred = np.zeros(len(y), int)
        for k in range(5):
            te = np.where(f == k)[0]; tr = np.where(f != k)[0]
            pred[te] = fit_predict(tr, X[te], seed).argmax(1)
        accs.append((pred == y).mean())
        if seed == 0: PRED = pred
    res.append((kind, np.mean(accs), np.std(accs)))
    pd.DataFrame({"template": M.template, "ok": PRED == y}).groupby("template").ok.mean().to_csv("../results/n2_cnn_per_template_%s.csv" % kind)
    print(kind, "accuracy %.3f +- %.3f" % res[-1][1:], "(%.0fs)" % (time.time() - t0), flush=True)
# sim-to-real
P = np.mean([fit_predict(np.arange(len(y)), XR, s) for s in range(3)], 0); pr = P.argmax(1)
py = (MR.language == "Python").values
print("sim-to-real, 61 real pairs: accuracy %.3f (majority 0.426); Python %.3f (n=%d); C/C++ %.3f (n=%d)" % ((pr == yR).mean(), (pr[py] == yR[py]).mean(), py.sum(), (pr[~py] == yR[~py]).mean(), (~py).sum()), flush=True)
cm = pd.crosstab(pd.Series(np.array(classes)[yR], name="true"), pd.Series(np.array(classes)[pr], name="predicted"))
print(cm.to_string())
pd.DataFrame(res, columns=["split", "accuracy", "sd"]).to_csv("../results/n2_cnn_code.csv", index=False)
cm.to_csv("../results/n2_cnn_sim2real_confusion.csv")
open("../results/n2_cnn_code.txt", "w").write("\n".join("%s %.3f +- %.3f" % r for r in res) + "\nsim-to-real accuracy %.3f python %.3f c %.3f\n" % ((pr == yR).mean(), (pr[py] == yR[py]).mean(), (pr[~py] == yR[~py]).mean()) + cm.to_string())
