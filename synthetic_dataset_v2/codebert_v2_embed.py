"""Frozen CodeBERT embeddings (mean-pooled, [CLS]) of the diffs parent -> child of the v2 debt introductions -> results/codebert_v2.npz. Run with the Python that has torch + transformers."""
import os, subprocess, sys, time
import numpy as np, pandas as pd, torch
from transformers import AutoModel, AutoTokenizer
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, "..", "insights", "new", "code"))
from n1_images import parse_diff
torch.set_num_threads(int(os.environ.get("THREADS", 4)))
P = pd.read_csv(os.path.join(HERE, "pairs.csv")); I = pd.read_csv(os.path.join(HERE, "instances.csv")).set_index("instance")
F = pd.read_csv(os.path.join(HERE, "features", "pairs_delta.csv"))[["instance"]]; P = F.merge(P, on="instance")
texts = []
for _, r in P.iterrows():
    t = subprocess.run(["git", "-C", os.path.join(HERE, "repos", r.project + ".git"), "diff", "-U0", r.parent, r.child], capture_output=True, text=True).stdout
    texts.append("\n".join(("+" if s > 0 else "-") + l for s, l in parse_diff(t, I.loc[r.instance].file)))
tok = AutoTokenizer.from_pretrained("microsoft/codebert-base"); model = AutoModel.from_pretrained("microsoft/codebert-base").eval()
M, C, t0 = [], [], time.time()
for i, t in enumerate(texts):
    ids = tok(t, add_special_tokens=False, truncation=False)["input_ids"] or [tok.unk_token_id]
    wins = [ids[k:k + 510] for k in range(0, len(ids), 510)][:3]
    m_acc, c_acc, w_acc = np.zeros(768), np.zeros(768), 0
    for w in wins:
        x = torch.tensor([[tok.cls_token_id] + w + [tok.sep_token_id]])
        with torch.no_grad():
            h = model(x).last_hidden_state[0]
        m_acc += h[1:-1].mean(0).numpy() * len(w); c_acc += h[0].numpy() * len(w); w_acc += len(w)
    M.append(m_acc / w_acc); C.append(c_acc / w_acc)
    if i % 100 == 0:
        print(i, len(texts), "%.0fs" % (time.time() - t0), flush=True)
os.makedirs(os.path.join(HERE, "results"), exist_ok=True)
np.savez_compressed(os.path.join(HERE, "results", "codebert_v2.npz"), mean=np.array(M, np.float32), cls=np.array(C, np.float32), instance=P.instance.values)
print("done", len(texts))
