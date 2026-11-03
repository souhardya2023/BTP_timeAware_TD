"""N9a: CodeBERT embeddings (frozen) of the changed lines of every debt introduction.
Text = the added (+) and removed (-) lines of the git diff parent -> child (the file of the debt first), the same text as the code images.
Long texts are cut into windows of 510 tokens (at most 4) and the embeddings of the windows are averaged.
Saves: mean-pooled and [CLS] embeddings, for the 1,321 synthetic pairs and the 61 real pairs.  Run with the Python that has transformers + torch."""
import os, subprocess, sys, time
import numpy as np, pandas as pd, torch
from transformers import AutoModel, AutoTokenizer
from sload import SD, ROOT
from n1_images import parse_diff
torch.set_num_threads(4)
def texts_synthetic():
    P = pd.read_csv(os.path.join(SD, "pairs.csv")); I = pd.read_csv(os.path.join(SD, "instances.csv")).set_index("instance")
    F = pd.read_csv(os.path.join(SD, "features", "pairs_delta.csv"))[["instance"]]; P = F.merge(P, on="instance")
    out = []
    for _, r in P.iterrows():
        t = subprocess.run(["git", "-C", os.path.join(SD, "repos", r.project + ".git"), "diff", "-U0", r.parent, r.child], capture_output=True, text=True).stdout
        out.append("\n".join(("+" if s > 0 else "-") + l for s, l in parse_diff(t, I.loc[r.instance].file)))
    return out
def texts_real():
    DS = pd.read_csv(os.path.join(ROOT, "out_dataset", "delta_only", "dataset_without_time.csv")); out = []
    for pid in DS.id:
        l, n = pid.split("/")
        patch = os.path.join(ROOT, "project_dataset", "Python" if l == "Python" else "C_C++", n, n + "_prop", "td.patch")
        out.append("\n".join(("+" if s > 0 else "-") + x for s, x in parse_diff(open(patch, errors="ignore").read())))
    return out
tok = AutoTokenizer.from_pretrained("microsoft/codebert-base"); model = AutoModel.from_pretrained("microsoft/codebert-base").eval()
def embed(texts, name):
    mean_e, cls_e, t0 = [], [], time.time()
    for i, t in enumerate(texts):
        ids = tok(t, add_special_tokens=False, truncation=False)["input_ids"] or [tok.unk_token_id]
        wins = [ids[k:k + 510] for k in range(0, len(ids), 510)][:4]
        m_acc, c_acc, w_acc = np.zeros(768), np.zeros(768), 0
        for w in wins:
            x = torch.tensor([[tok.cls_token_id] + w + [tok.sep_token_id]])
            with torch.no_grad(): h = model(x).last_hidden_state[0]
            m_acc += h[1:-1].mean(0).numpy() * len(w); c_acc += h[0].numpy() * len(w); w_acc += len(w)
        mean_e.append(m_acc / w_acc); cls_e.append(c_acc / w_acc)
        if i % 100 == 0: print(name, i, len(texts), "%.0fs" % (time.time() - t0), "tokens", len(ids), flush=True)
    return np.array(mean_e, np.float32), np.array(cls_e, np.float32)
TS, TR = texts_synthetic(), texts_real()
print("texts", len(TS), len(TR), "mean chars", np.mean([len(t) for t in TS]), flush=True)
ms, cs = embed(TS, "synthetic"); mr, cr = embed(TR, "real")
np.savez_compressed("../results/n9_codebert.npz", ms=ms, cs=cs, mr=mr, cr=cr)
print("done", ms.shape, mr.shape)
