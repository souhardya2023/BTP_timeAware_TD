#!/usr/bin/env python3
"""Frozen embeddings of the same texts (../embeddings/texts.pkl) from one foundation model -> ../embeddings/<name>.npz
usage: e1_embed.py NAME            NAME in MODELS below. Run with the Python that has torch + transformers (CPU).
Only standard transformers classes are used (no remote code is executed).
Text longer than 254 tokens is cut at 254 tokens (one window, to save CPU time).
'mean' = mean over tokens of the last layer; 'cls' = first-token state (encoders) or last-token state (decoder)."""
import os, pickle, sys, time
import numpy as np, torch
from transformers import AutoModel, AutoTokenizer, T5EncoderModel

torch.set_num_threads(int(os.environ.get("THREADS", 4)))
HERE = os.path.dirname(os.path.abspath(__file__)); EMB = os.path.join(HERE, "..", "embeddings")
MODELS = {  # name: (hf id, family)
    "codebert": ("microsoft/codebert-base", "enc"),
    "graphcodebert": ("microsoft/graphcodebert-base", "enc"),
    "unixcoder": ("microsoft/unixcoder-base", "enc"),
    "roberta": ("FacebookAI/roberta-base", "enc"),
    "codet5": ("Salesforce/codet5-base", "t5enc"),
    "qwen_coder": ("Qwen/Qwen2.5-Coder-0.5B", "dec"),
}
MAXW, WLEN, BS = 1, 254, 16


def main():
    name = sys.argv[1]; hf, fam = MODELS[name]
    d = pickle.load(open(os.path.join(EMB, "texts.pkl"), "rb"))
    texts = d["natural"] + d["synthetic"] + d["real"]
    tok = AutoTokenizer.from_pretrained(hf)
    if fam == "t5enc": model = T5EncoderModel.from_pretrained(hf).eval()
    else: model = AutoModel.from_pretrained(hf, dtype=torch.bfloat16 if fam == "dec" else torch.float32).eval()
    items = []  # (text index, ids)
    for i, t in enumerate(texts):
        ids = tok(t, add_special_tokens=False, truncation=False)["input_ids"] or [tok.unk_token_id or 0]
        for k in range(0, min(len(ids), MAXW * WLEN), WLEN): items.append((i, ids[k:k + WLEN]))
    order = sorted(range(len(items)), key=lambda j: len(items[j][1]))
    n = len(texts); acc_m = acc_c = None; wsum = np.zeros(n); t0 = time.time()
    cls_id = tok.cls_token_id if tok.cls_token_id is not None else tok.bos_token_id
    sep_id = tok.sep_token_id if tok.sep_token_id is not None else tok.eos_token_id
    pad = tok.pad_token_id if tok.pad_token_id is not None else 0
    wrap = fam in ("enc", "t5enc") and cls_id is not None and sep_id is not None
    for b in range(0, len(order), BS):
        sel = [items[j] for j in order[b:b + BS]]
        seqs = [([cls_id] + ids + [sep_id]) if wrap else ids for _, ids in sel]
        L = max(len(s) for s in seqs)
        x = torch.tensor([s + [pad] * (L - len(s)) for s in seqs]); m = torch.tensor([[1] * len(s) + [0] * (L - len(s)) for s in seqs])
        with torch.no_grad():
            h = model(input_ids=x, attention_mask=m).last_hidden_state.float()
        lo = 1 if wrap else 0
        M = np.stack([h[r, lo:(len(s) - 1 if wrap else len(s))].mean(0).numpy() for r, s in enumerate(seqs)])
        C = np.stack([h[r, 0 if fam != "dec" else len(s) - 1].numpy() for r, s in enumerate(seqs)])
        if acc_m is None: acc_m = np.zeros((n, M.shape[1])); acc_c = np.zeros((n, M.shape[1]))
        for r, (i, ids) in enumerate(sel):
            acc_m[i] += M[r] * len(ids); acc_c[i] += C[r] * len(ids); wsum[i] += len(ids)
        if (b // BS) % 25 == 0: print(name, b, len(order), "%.0fs" % (time.time() - t0), flush=True)
    np.savez_compressed(os.path.join(EMB, name + ".npz"), mean=(acc_m / wsum[:, None]).astype(np.float32), cls=(acc_c / wsum[:, None]).astype(np.float32),
                        n_natural=len(d["natural"]), n_synthetic=len(d["synthetic"]), n_real=len(d["real"]))
    print("done", name, acc_m.shape[1], "%.0fs" % (time.time() - t0))


if __name__ == "__main__":
    main()
