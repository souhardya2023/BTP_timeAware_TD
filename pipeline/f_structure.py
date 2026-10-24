"""STRUCTURE block: directory layout, module/include dependency graph (size, cycles, centrality, community structure, spectrum, WL histogram)."""
import hashlib
import math
import os
import re
from collections import Counter, defaultdict

import networkx as nx
import numpy as np

from common import EXT, gini, log1p, quant, read, src_files

WL_BINS = 32
SPEC_K = 6


def py_graph(root, files):
    mods = {}
    for rel, p, lang in files:
        if lang != "py":
            continue
        m = rel[:-3].replace(os.sep, ".")
        if m.endswith(".__init__"):
            m = m[: -len(".__init__")]
        if m.startswith("src."):
            m = m[4:]
        mods[m] = rel
    g = nx.DiGraph()
    g.add_nodes_from(mods.values())
    import ast
    for m, rel in mods.items():
        try:
            tree = ast.parse(read(os.path.join(root, rel)))
        except (SyntaxError, ValueError):
            continue
        is_pkg = rel.endswith("__init__.py")
        parts = m.split(".")
        for node in ast.walk(tree):
            targets = []
            if isinstance(node, ast.Import):
                targets = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom):
                if node.level:
                    cut = node.level - (1 if is_pkg else 0)
                    pre = ".".join(parts[: len(parts) - cut] if cut else parts)
                    targets = [(pre + "." + node.module if pre else node.module)] if node.module else [(pre + "." + a.name if pre else a.name) for a in node.names]
                elif node.module:
                    targets = [node.module]
            for t in targets:
                while t and t not in mods:
                    t = t.rpartition(".")[0]
                if t and mods[t] != rel:
                    g.add_edge(rel, mods[t])
    return g


def c_graph(root, files):
    names = {rel: rel for rel, _, lang in files}
    by_base = defaultdict(list)
    for rel in names:
        by_base[os.path.basename(rel)].append(rel)
    g = nx.DiGraph()
    g.add_nodes_from(names)
    inc = re.compile(r'^\s*#\s*include\s+"([^"]+)"', re.M)
    for rel, p, _ in files:
        for m in inc.findall(read(p)):
            for c in by_base.get(os.path.basename(m), []):
                if c != rel:
                    g.add_edge(rel, c)
    return g


def wl_hist(g, iters=3):
    """Weisfeiler-Lehman subtree label histogram hashed to WL_BINS bins (normalised)."""
    lab = {n: f"{min(g.in_degree(n), 6)}/{min(g.out_degree(n), 6)}/{os.path.splitext(n)[1]}" for n in g}
    h = np.zeros(WL_BINS)
    for _ in range(iters):
        new = {}
        for n in g:
            s = lab[n] + "|" + ",".join(sorted(lab[x] for x in g.successors(n))) + "|" + ",".join(sorted(lab[x] for x in g.predecessors(n)))
            new[n] = hashlib.md5(s.encode()).hexdigest()[:10]
            h[int(new[n], 16) % WL_BINS] += 1
        lab = new
    return h / max(h.sum(), 1)


def graph_features(g):
    f = {}
    n, e = g.number_of_nodes(), g.number_of_edges()
    f["graph_nodes"], f["graph_edges"] = log1p(n), log1p(e)
    f["graph_density"] = e / (n * (n - 1)) if n > 1 else 0.0
    f["graph_edges_per_node"] = e / n if n else 0.0
    sccs = [c for c in nx.strongly_connected_components(g) if len(c) > 1]
    f["cyc_groups"] = len(sccs)
    f["cyc_nodes_share"] = sum(len(c) for c in sccs) / n if n else 0.0
    f["cyc_largest"] = max((len(c) for c in sccs), default=0) / n if n else 0.0
    indeg = [d for _, d in g.in_degree()]
    outdeg = [d for _, d in g.out_degree()]
    f.update(quant(indeg, "fan_in", (0.5, 0.9, 1.0)))
    f.update(quant(outdeg, "fan_out", (0.5, 0.9, 1.0)))
    f["fan_in_gini"], f["fan_out_gini"] = gini(indeg), gini(outdeg)
    inst = [o / (i + o) for i, o in zip(indeg, outdeg) if i + o > 0]
    f["instability_mean"] = float(np.mean(inst)) if inst else 0.0
    f["isolated_share"] = sum(1 for i, o in zip(indeg, outdeg) if i + o == 0) / n if n else 0.0
    # condensation depth (longest dependency chain once cycles are collapsed)
    try:
        c = nx.condensation(g)
        f["dep_depth"] = nx.dag_longest_path_length(c) / max(math.log2(n + 1), 1) if n else 0.0
    except Exception:
        f["dep_depth"] = 0.0
    u = g.to_undirected()
    f["weak_components"] = nx.number_connected_components(u) / n if n else 0.0
    if n >= 3 and e >= 2:
        big = u.subgraph(max(nx.connected_components(u), key=len))
        f["clustering"] = nx.average_clustering(big)
        try:
            comms = nx.community.greedy_modularity_communities(big)
            f["modularity"] = nx.community.modularity(big, comms)
            f["communities"] = len(comms) / max(len(big), 1)
        except Exception:
            f["modularity"], f["communities"] = 0.0, 0.0
        try:
            f["assortativity"] = float(np.nan_to_num(nx.degree_assortativity_coefficient(big)))
        except Exception:
            f["assortativity"] = 0.0
        pr = np.array(list(nx.pagerank(g, max_iter=100).values()))
        f["pagerank_max"] = float(pr.max() * n)
        f["pagerank_entropy"] = float(-(pr * np.log(pr + 1e-12)).sum() / math.log(n)) if n > 1 else 0.0
        # normalised-Laplacian spectrum of the largest component (smallest SPEC_K non-trivial eigenvalues)
        try:
            L = nx.normalized_laplacian_matrix(big).toarray() if len(big) <= 1200 else None
            ev = np.sort(np.linalg.eigvalsh(L))[1:SPEC_K + 1] if L is not None else np.zeros(SPEC_K)
        except Exception:
            ev = np.zeros(SPEC_K)
        ev = np.pad(ev, (0, SPEC_K - len(ev)))
        for i, v in enumerate(ev):
            f[f"spec_{i}"] = float(v)
    else:
        for k in ("clustering", "modularity", "communities", "assortativity", "pagerank_max", "pagerank_entropy"):
            f[k] = 0.0
        for i in range(SPEC_K):
            f[f"spec_{i}"] = 0.0
    return f


def tree_features(root, files):
    f = {}
    dirs = Counter(os.path.dirname(rel) for rel, _, _ in files)
    depth = [rel.count(os.sep) for rel, _, _ in files]
    sizes = [len(read(p)) for _, p, _ in files]
    f["files"] = log1p(len(files))
    f["dirs"] = log1p(len(dirs))
    f["files_per_dir_mean"] = float(np.mean(list(dirs.values()))) if dirs else 0.0
    f["files_per_dir_max"] = float(max(dirs.values())) if dirs else 0.0
    f["depth_mean"], f["depth_max"] = (float(np.mean(depth)), float(max(depth))) if depth else (0.0, 0.0)
    f.update(quant([math.log1p(s) for s in sizes], "file_bytes_log", (0.5, 0.9, 1.0)))
    f["file_size_gini"] = gini(sizes)
    f["share_headers"] = sum(1 for rel, _, _ in files if rel.endswith((".h", ".hpp"))) / len(files) if files else 0.0
    f["share_init"] = sum(1 for rel, _, _ in files if rel.endswith("__init__.py")) / len(files) if files else 0.0
    return f


def structure(root, files, lang):
    g = py_graph(root, files) if lang == "py" else c_graph(root, files)
    f = {"s_" + k: v for k, v in tree_features(root, files).items()}
    f.update({"s_" + k: v for k, v in graph_features(g).items()})
    return f, wl_hist(g), g
