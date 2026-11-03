#!/usr/bin/env python3
"""Frozen CodeBERT embeddings (mean-pooled and [CLS]) of the diffs of the natural pairs (results/b1_diffs.jsonl) -> results/b2_codebert.npz. Run with a Python that has torch + transformers."""
import json, os, time
import numpy as np, torch
from transformers import AutoModel, AutoTokenizer
torch.set_num_threads(int(os.environ.get("THREADS", 3)))
R = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")
rows = [json.loads(l) for l in open(os.path.join(R, "b1_diffs.jsonl"))]
tok = AutoTokenizer.from_pretrained("microsoft/codebert-base"); model = AutoModel.from_pretrained("microsoft/codebert-base").eval()
M, Cc, t0 = [], [], time.time()
for i, r in enumerate(rows):
    ids = tok(r["text"], add_special_tokens=False, truncation=False)["input_ids"] or [tok.unk_token_id]
    wins = [ids[k:k + 510] for k in range(0, len(ids), 510)][:3]
    m_acc, c_acc, w_acc = np.zeros(768), np.zeros(768), 0
    for w in wins:
        x = torch.tensor([[tok.cls_token_id] + w + [tok.sep_token_id]])
        with torch.no_grad():
            h = model(x).last_hidden_state[0]
        m_acc += h[1:-1].mean(0).numpy() * len(w); c_acc += h[0].numpy() * len(w); w_acc += len(w)
    M.append(m_acc / w_acc); Cc.append(c_acc / w_acc)
    if i % 100 == 0:
        print(i, len(rows), "%.0fs" % (time.time() - t0), flush=True)
np.savez_compressed(os.path.join(R, "b2_codebert.npz"), mean=np.array(M, np.float32), cls=np.array(Cc, np.float32), keys=np.array([r["repo"] + "|" + r["sha"] for r in rows]))
print("done")
