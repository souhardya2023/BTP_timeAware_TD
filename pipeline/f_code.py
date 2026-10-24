"""CODE block: every line of code summarised - LOC/SLOC/comments, per-function size/complexity distributions,
syntax-kind histogram (hashed), language-specific idioms, and an identifier bag-of-words (hashed) for the learned code embedding.

`analyze(root, files)` is run once per snapshot and its result (`ctx`) is shared with the TD block.
"""
import ast
import hashlib
import math
import re
from collections import Counter

import lizard
import numpy as np

from common import log1p, quant, read

SYN_BINS = 32
BAG_BINS = 4096
IDENT = re.compile(r"[A-Za-z_][A-Za-z0-9_]{2,}")
CAMEL = re.compile(r"[A-Z]+(?![a-z])|[A-Z]?[a-z]+|\d+")
STOP = set("the and for def self return import from class none true false not with elif else try except raise pass lambda yield int char void const static struct unsigned sizeof include define ifdef endif ifndef".split())
C_KW = ("if", "else", "for", "while", "do", "switch", "case", "break", "continue", "return", "goto", "struct", "union", "enum", "typedef", "static", "const",
        "sizeof", "extern", "inline", "volatile", "unsigned", "signed", "void", "char", "int", "long", "short", "float", "double")


def h(s, bins):
    return int(hashlib.md5(s.encode()).hexdigest()[:8], 16) % bins


def tokens_of(text):
    out = []
    for w in IDENT.findall(text):
        for p in CAMEL.findall(w.replace("_", " ")):
            p = p.lower()
            if len(p) > 2 and p not in STOP and not p.isdigit():
                out.append(p)
    return out


def comments_of(text, lang):
    if lang == "py":
        return [m.group(1).strip() for m in re.finditer(r"#\s*(.*)", text)]
    return [m.group(1).strip() for m in re.finditer(r"//\s*(.*)", text)] + [m.group(1).strip() for m in re.finditer(r"/\*(.*?)\*/", text, re.S)]


def analyze(root, files):
    import os
    funcs, fmeta, comments = [], [], []
    bag, syn = Counter(), np.zeros(SYN_BINS)
    idioms = Counter()
    for rel, p, lang in files:
        text = read(p)
        lines = text.split("\n")
        blank = sum(1 for l in lines if not l.strip())
        cm = comments_of(text, lang)
        comments += [(rel, c) for c in cm]
        if lang == "py":
            cl = sum(1 for l in lines if l.strip().startswith("#"))
        else:
            cl = sum(1 for l in lines if l.strip().startswith(("//", "/*", "*")))
        try:
            info = lizard.analyze_file.analyze_source_code(rel, text)
            nloc = info.nloc
            for fn in info.function_list:
                funcs.append(dict(file=rel, name=fn.name, s=fn.start_line, e=fn.end_line, nloc=fn.nloc, ccn=fn.cyclomatic_complexity,
                                  par=len(fn.parameters), tok=fn.token_count, lang=lang))
        except Exception:
            nloc = len(lines) - blank - cl
        indent = [len(l) - len(l.lstrip()) for l in lines if l.strip()]
        fmeta.append(dict(file=rel, lang=lang, loc=len(lines), blank=blank, comment=cl, sloc=nloc, max_indent=max(indent) if indent else 0,
                          mean_indent=float(np.mean(indent)) if indent else 0.0, bytes=len(text)))
        for t in tokens_of(text):
            bag[h(t, BAG_BINS)] += 1
        if lang == "py":
            try:
                tree = ast.parse(text)
            except (SyntaxError, ValueError):
                continue
            nfun = 0
            for node in ast.walk(tree):
                syn[h(type(node).__name__, SYN_BINS)] += 1
                if isinstance(node, ast.ClassDef):
                    idioms["classes"] += 1
                    idioms["methods"] += sum(isinstance(b, (ast.FunctionDef, ast.AsyncFunctionDef)) for b in node.body)
                    if ast.get_docstring(node):
                        idioms["doc_classes"] += 1
                elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    nfun += 1
                    idioms["pyfuncs"] += 1
                    idioms["annotated"] += int(node.returns is not None or any(a.annotation for a in node.args.args))
                    idioms["doc_funcs"] += int(bool(ast.get_docstring(node)))
                    idioms["decorated"] += int(bool(node.decorator_list))
                    idioms["async"] += int(isinstance(node, ast.AsyncFunctionDef))
                elif isinstance(node, ast.Try):
                    idioms["try"] += 1
                    idioms["bare_except"] += sum(1 for hd in node.handlers if hd.type is None)
                elif isinstance(node, ast.Raise):
                    idioms["raise"] += 1
                elif isinstance(node, ast.Lambda):
                    idioms["lambda"] += 1
                elif isinstance(node, ast.Global):
                    idioms["global"] += 1
        else:
            for w in re.findall(r"[A-Za-z_]+|->|\+\+|--|&&|\|\||[<>=!]=|<<|>>", text):
                if w in C_KW or not w[0].isalpha() and w[0] != "_":
                    syn[h(w, SYN_BINS)] += 1
            idioms["defines"] += len(re.findall(r"^\s*#\s*define", text, re.M))
            idioms["ifdefs"] += len(re.findall(r"^\s*#\s*if", text, re.M))
            idioms["goto"] += len(re.findall(r"\bgoto\b", text))
            idioms["alloc"] += len(re.findall(r"\b(malloc|calloc|realloc|free)\s*\(", text))
            idioms["arrow"] += len(re.findall(r"->", text))
            idioms["casts"] += len(re.findall(r"\(\s*(?:const\s+)?\w+\s*\*+\s*\)", text))
            idioms["statics"] += len(re.findall(r"^\s*static\b", text, re.M))
            idioms["asserts"] += len(re.findall(r"\bassert\s*\(", text))
    return dict(funcs=funcs, fmeta=fmeta, comments=comments, bag=bag, syn=syn / max(syn.sum(), 1), idioms=idioms, files=files)


def code_features(ctx):
    f = {}
    fm, fn = ctx["fmeta"], ctx["funcs"]
    sloc = sum(m["sloc"] for m in fm)
    loc = sum(m["loc"] for m in fm)
    f["c_loc"], f["c_sloc"] = log1p(loc), log1p(sloc)
    f["c_comment_ratio"] = sum(m["comment"] for m in fm) / max(loc, 1)
    f["c_blank_ratio"] = sum(m["blank"] for m in fm) / max(loc, 1)
    f.update({"c_" + k: v for k, v in quant([math.log1p(m["sloc"]) for m in fm], "file_sloc_log", (0.5, 0.9, 1.0)).items()})
    f["c_big_files"] = sum(1 for m in fm if m["sloc"] > 1000) / max(len(fm), 1)
    f["c_indent_max"] = float(max((m["max_indent"] for m in fm), default=0))
    f["c_indent_mean"] = float(np.mean([m["mean_indent"] for m in fm])) if fm else 0.0
    f["c_functions"] = log1p(len(fn))
    f["c_funcs_per_kloc"] = len(fn) / max(sloc / 1000, 1e-3)
    for key, qs in (("nloc", (0.5, 0.9, 1.0)), ("ccn", (0.5, 0.9, 1.0)), ("par", (0.5, 0.9, 1.0)), ("tok", (0.5, 0.9))):
        f.update({"c_fn_" + k: v for k, v in quant([x[key] for x in fn], key, qs).items()})
    f["c_fn_nloc_std"] = float(np.std([x["nloc"] for x in fn])) if fn else 0.0
    f["c_fn_ccn_sum_per_kloc"] = sum(x["ccn"] for x in fn) / max(sloc / 1000, 1e-3)
    f["c_fn_short_share"] = sum(1 for x in fn if x["nloc"] <= 5) / max(len(fn), 1)
    I = ctx["idioms"]
    pf = max(I["pyfuncs"], 1)
    f["c_py_classes"] = log1p(I["classes"])
    f["c_py_methods_per_class"] = I["methods"] / max(I["classes"], 1)
    f["c_py_annotated"] = I["annotated"] / pf
    f["c_py_doc_funcs"] = I["doc_funcs"] / pf
    f["c_py_doc_classes"] = I["doc_classes"] / max(I["classes"], 1)
    f["c_py_decorated"] = I["decorated"] / pf
    f["c_py_async"] = I["async"] / pf
    f["c_py_try_per_kloc"] = I["try"] / max(sloc / 1000, 1e-3)
    f["c_py_bare_except_per_kloc"] = I["bare_except"] / max(sloc / 1000, 1e-3)
    f["c_py_raise_per_kloc"] = I["raise"] / max(sloc / 1000, 1e-3)
    f["c_py_lambda_per_kloc"] = I["lambda"] / max(sloc / 1000, 1e-3)
    for k in ("defines", "ifdefs", "goto", "alloc", "arrow", "casts", "statics", "asserts"):
        f["c_c_" + k + "_per_kloc"] = I[k] / max(sloc / 1000, 1e-3)
    return f
