"""Insight set L2-A: how does interest behave over time and space?  (descriptive, no model)
 1. concentration of interest (Pareto / Gini)
 2. memory: P(interest in release t+1 | interest in release t-l) for lags l, against the base rate
 3. hazard of interest by age of the instance and by time since the region was last changed
 4. spatial contagion: if another debt instance in the SAME FILE paid interest last release, does this one pay more?
 5. burstiness of projects: is interest concentrated in a few releases?
"""
import numpy as np
import pandas as pd
from common import load_transitions

df = load_transitions()
out = []
P = lambda s: out.append(s)

# ---------- 1. concentration
ev = df[df.y > 0]
tot = ev.y.sum()
inst = df.groupby(["repo", "key"]).y.sum().sort_values(ascending=False)
inst_pos = inst[inst > 0]
n_inst = len(inst)
cum = inst.cumsum() / tot
P("## 1. Concentration of interest")
P(f"instances: {n_inst}; instances that ever paid interest: {len(inst_pos)} ({len(inst_pos)/n_inst:.1%}); instance-releases with interest: {(df.y>0).mean():.1%}")
for q in (0.01, 0.05, 0.10, 0.20):
    m = max(1, int(round(q * n_inst)))
    P(f"top {q:.0%} of instances ({m}) hold {cum.iloc[m-1]:.1%} of all interest")
x = np.sort(inst.values)
gini = 1 - 2 * np.sum((np.cumsum(x) - x / 2)) / (len(x) * x.sum()) if x.sum() > 0 else float("nan")
P(f"Gini of interest over instances: {gini:.3f}")
fil = df.groupby(["repo", "file"]).y.sum()
P(f"files holding interest: {(fil>0).sum()} of {len(fil)} files with a debt instance; top 10% of files hold {fil.sort_values(ascending=False).iloc[:max(1,int(0.1*len(fil)))].sum()/tot:.1%}")

# ---------- 2. memory (lag structure)
P("\n## 2. Memory: P(interest at t | interest at t-lag) per instance")
base = (df.y > 0).mean()
P(f"base rate P(interest) = {base:.3f}")
d = df[["repo", "key", "vi", "any"]].copy()
rows = []
for lag in range(1, 7):
    s = d.copy(); s["vi"] = s["vi"] + lag
    m = d.merge(s.rename(columns={"any": "prev"}), on=["repo", "key", "vi"])
    a = m[m.prev == 1]["any"].mean(); b = m[m.prev == 0]["any"].mean()
    rows.append((lag, len(m), a, b, a / b if b else np.nan))
    P(f"lag {lag}: n={len(m)} P(int | int at t-{lag}) = {a:.3f}, P(int | none at t-{lag}) = {b:.3f}, ratio {a/b:.1f}")
mem = pd.DataFrame(rows, columns=["lag", "n", "p_given_event", "p_given_none", "ratio"])
mem.to_csv("../results/l2_memory_lags.csv", index=False)

# ---------- 3. hazard by age and by time since last change of the region
P("\n## 3. Hazard of interest in the next release")
df["age_b"] = pd.cut(df.age, [-1, 0, 1, 2, 4, 8, 20], labels=["0", "1", "2", "3-4", "5-8", "9+"])
h = df.groupby("age_b", observed=True)["any"].agg(["mean", "size"])
P("by age (releases since the instance appeared):\n" + h.round(3).to_string())
h.to_csv("../results/l2_hazard_age.csv")
df["ever"] = (df.past_il > 0).map({True: "paid interest before", False: "never paid"})
h2 = df.groupby("ever")["any"].agg(["mean", "size"])
P("by history:\n" + h2.round(3).to_string())
df["pn_b"] = pd.cut(df.past_n, [-1, 0, 1, 2, 4, 100], labels=["0", "1", "2", "3-4", "5+"])
h3 = df.groupby("pn_b", observed=True)["any"].agg(["mean", "size"])
P("by number of past interest events:\n" + h3.round(3).to_string())
h3.to_csv("../results/l2_hazard_pastn.csv")

# ---------- 4. spatial contagion inside a file
P("\n## 4. Spatial contagion: do instances in the same file pay interest together?")
d = df[["repo", "file", "key", "vi", "any", "interest_lines"]].copy()
file_prev = d.groupby(["repo", "file", "vi"]).agg(f_int=("interest_lines", "sum"), f_n=("key", "size")).reset_index()
s = file_prev.copy(); s["vi"] = s["vi"] + 1                       # activity of the file in the previous release pair
m = d.merge(s.rename(columns={"f_int": "file_prev_il", "f_n": "file_prev_n"}), on=["repo", "file", "vi"], how="left").fillna({"file_prev_il": 0, "file_prev_n": 0})
# remove the instance's own previous interest to isolate the neighbours
own = d[["repo", "key", "vi", "interest_lines"]].copy(); own["vi"] += 1
m = m.merge(own.rename(columns={"interest_lines": "own_prev"}), on=["repo", "key", "vi"], how="left").fillna({"own_prev": 0})
m["nbr_prev"] = m.file_prev_il - m.own_prev
sub = m[(m.own_prev == 0) & (m.file_prev_n > 1)]
a = sub[sub.nbr_prev > 0]["any"].mean(); b = sub[sub.nbr_prev == 0]["any"].mean()
P(f"instances that did not pay interest last release and share a file with other instances (n={len(sub)}):")
P(f"  P(interest) if a neighbour in the file paid last release = {a:.3f} (n={int((sub.nbr_prev>0).sum())});  if no neighbour paid = {b:.3f};  ratio {a/b:.1f}")
sub2 = m[(m.own_prev > 0)]
P(f"  for comparison, instances that paid themselves last release: P = {sub2['any'].mean():.3f} (n={len(sub2)})")
m[["repo", "key", "vi", "nbr_prev", "own_prev", "any"]].to_csv("../results/l2_neighbour_table.csv", index=False)

# ---------- 5. burstiness over releases
P("\n## 5. Burstiness of interest over releases (per project)")
rel = df.groupby(["repo", "vi"]).y.sum().reset_index()
rows = []
for r, g in rel.groupby("repo"):
    v = g.y.values
    rows.append((r, len(v), v.sum(), np.sort(v)[::-1][:max(1, len(v)//5)].sum() / v.sum(), v.std() / v.mean(), (v == 0).mean()))
b = pd.DataFrame(rows, columns=["repo", "releases", "total_mPM", "top20pct_releases_share", "cv", "zero_release_share"])
P(b.round(3).to_string(index=False))
b.to_csv("../results/l2_burstiness.csv", index=False)
open("../results/l2_temporal_structure.txt", "w").write("\n".join(out))
print("\n".join(out))
