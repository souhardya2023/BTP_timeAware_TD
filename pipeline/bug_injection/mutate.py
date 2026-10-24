"""Candidate bugs (semantic mutations) for Python and C sources.

Every mutant is ONE small behaviour change in one function:
  cmp_boundary   <  <->  <=      >  <->  >=         (off-by-one at a boundary)
  cmp_equality   == <-> !=
  bool_op        and <-> or      && <-> ||
  arith          + <-> -   (Python binary operations),   '+ 1' <-> '- 1' (C)
  negate_cond    if (c)  ->  if (not c)
  const_off_by_one   an integer literal in a comparison / index / range() gets +1

mutants(rel, text, lang) -> [dict(file, line, op, func, desc, new_text)]   (new_text = the whole mutated file)
patch_of(rel, old, new)  -> a unified diff that `git apply` / `patch -p1` accept on any copy of the project
"""
import ast
import difflib
import re

import lizard


def patch_of(rel, old, new):
    d = difflib.unified_diff(old.splitlines(True), new.splitlines(True), f"a/{rel}", f"b/{rel}", n=3)
    out = "".join(d)
    return out if out.endswith("\n") else out + "\n"


# ------------------------------------------------------------------------------------------------ Python
def _offsets(src):
    offs, o = [], 0
    for line in src.split(b"\n"):
        offs.append(o)
        o += len(line) + 1
    return offs


def py_mutants(rel, text):
    try:
        tree = ast.parse(text)
    except (SyntaxError, ValueError):
        return []
    src = text.encode("utf-8")
    offs = _offsets(src)
    P = lambda l, c: offs[l - 1] + c
    funcs = sorted(((n.lineno, getattr(n, "end_lineno", n.lineno), n.name) for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))),
                   key=lambda x: x[1] - x[0])

    def fname(line):
        for s, e, n in funcs:
            if s <= line <= e:
                return n
        return None

    out = []

    def add(line, op, a, b, new_bytes, desc):
        fn = fname(line)
        if fn is None:                          # only inside functions
            return
        new = (src[:a] + new_bytes + src[b:]).decode("utf-8", "replace")
        try:
            ast.parse(new)
        except (SyntaxError, ValueError):
            return
        if new != text:
            out.append(dict(file=rel, line=line, op=op, func=fn, desc=desc, new_text=new))

    def gap(left, right):
        return P(left.end_lineno, left.end_col_offset), P(right.lineno, right.col_offset)

    CMP = {ast.Lt: ("<", "<=", "cmp_boundary"), ast.LtE: ("<=", "<", "cmp_boundary"), ast.Gt: (">", ">=", "cmp_boundary"), ast.GtE: (">=", ">", "cmp_boundary"),
           ast.Eq: ("==", "!=", "cmp_equality"), ast.NotEq: ("!=", "==", "cmp_equality")}
    for node in ast.walk(tree):
        if isinstance(node, ast.Compare):
            left = node.left
            for op, right in zip(node.ops, node.comparators):
                if type(op) in CMP:
                    old, new, name = CMP[type(op)]
                    a, b = gap(left, right)
                    seg = src[a:b].decode("utf-8", "replace")
                    k = seg.find(old)
                    if k >= 0 and (old not in ("<", ">") or seg[k:k + 2] not in ("<=", ">=")):
                        add(node.lineno, name, a + k, a + k + len(old), new.encode(), f"`{old}` -> `{new}` in a comparison in {fname(node.lineno)}()")
                left = right
        elif isinstance(node, ast.BoolOp):
            old, new = ("and", "or") if isinstance(node.op, ast.And) else ("or", "and")
            for v1, v2 in zip(node.values, node.values[1:]):
                a, b = gap(v1, v2)
                seg = src[a:b].decode("utf-8", "replace")
                k = seg.find(old)
                if k >= 0:
                    add(node.lineno, "bool_op", a + k, a + k + len(old), new.encode(), f"`{old}` -> `{new}` in a condition in {fname(node.lineno)}()")
        elif isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Sub)):
            a, b = gap(node.left, node.right)
            seg = src[a:b].decode("utf-8", "replace")
            old, new = ("+", "-") if isinstance(node.op, ast.Add) else ("-", "+")
            k = seg.find(old)
            if k >= 0:
                add(node.lineno, "arith", a + k, a + k + 1, new.encode(), f"`{old}` -> `{new}` in an expression in {fname(node.lineno)}()")
        elif isinstance(node, (ast.If, ast.While)):
            t = node.test
            a, b = P(t.lineno, t.col_offset), P(t.end_lineno, t.end_col_offset)
            add(t.lineno, "negate_cond", a, b, b"not (" + src[a:b] + b")", f"condition negated in {fname(t.lineno)}()")
        elif isinstance(node, ast.Constant) and isinstance(node.value, int) and not isinstance(node.value, bool):
            pass
    # integer literals that are part of a comparison, subscript or range()
    for node in ast.walk(tree):
        subs = []
        if isinstance(node, ast.Compare):
            subs = [node.left] + node.comparators
        elif isinstance(node, ast.Subscript):
            subs = [node.slice]
        elif isinstance(node, ast.Call) and getattr(node.func, "id", "") == "range":
            subs = node.args
        for s in subs:
            for c in ast.walk(s):
                if isinstance(c, ast.Constant) and isinstance(c.value, int) and not isinstance(c.value, bool) and c.value >= 0:
                    a, b = P(c.lineno, c.col_offset), P(c.end_lineno, c.end_col_offset)
                    add(c.lineno, "const_off_by_one", a, b, str(c.value + 1).encode(), f"constant {c.value} -> {c.value + 1} in {fname(c.lineno)}()")
    return out


# ------------------------------------------------------------------------------------------------ C
REL = {"<=": ("<", "cmp_boundary"), ">=": (">", "cmp_boundary"), "<": ("<=", "cmp_boundary"), ">": (">=", "cmp_boundary"),
       "==": ("!=", "cmp_equality"), "!=": ("==", "cmp_equality"), "&&": ("||", "bool_op"), "||": ("&&", "bool_op")}
TOK = re.compile(r"<=|>=|==|!=|&&|\|\||(?<![<>\-])<(?![<=])|(?<![<>\-])>(?![>=])")


def _in_string(s, pos):
    return s[:pos].count('"') % 2 == 1 or s[:pos].count("'") % 2 == 1


def _cond(line):
    """(start, end) of the parenthesised condition of the first if/while on the line, or None."""
    m = re.search(r"\b(if|while)\s*\(", line)
    if not m or _in_string(line, m.start()):
        return None
    depth, i = 1, m.end()
    while i < len(line) and depth:
        depth += (line[i] == "(") - (line[i] == ")")
        i += 1
    return (m.end(), i - 1) if depth == 0 else None


def c_mutants(rel, text):
    try:
        info = lizard.analyze_file.analyze_source_code(rel, text)
    except Exception:
        return []
    lines = text.split("\n")
    out = []

    def add(i, op, new_line, func, desc):
        if new_line != lines[i]:
            nl = lines[:i] + [new_line] + lines[i + 1:]
            out.append(dict(file=rel, line=i + 1, op=op, func=func, desc=desc, new_text="\n".join(nl)))

    for fn in info.function_list:
        for i in range(fn.start_line, fn.end_line):          # the body lines (0-based index of line i+1)
            l = lines[i]
            s = l.strip()
            if not s or s.startswith(("#", "//", "/*", "*")):
                continue
            c = _cond(l)
            if c:
                a, b = c
                cond = l[a:b]
                for m in TOK.finditer(cond):
                    if _in_string(cond, m.start()):
                        continue
                    new, name = REL[m.group()]
                    add(i, name, l[:a] + cond[:m.start()] + new + cond[m.end():] + l[b:], fn.name, f"`{m.group()}` -> `{new}` in a condition in {fn.name}()")
                    break
                add(i, "negate_cond", l[:a] + "!(" + cond + ")" + l[b:], fn.name, f"condition negated in {fn.name}()")
                for m in re.finditer(r"(?<![\w.])(\d+)(?![\w.])", cond):
                    if not _in_string(cond, m.start()):
                        v = int(m.group(1))
                        add(i, "const_off_by_one", l[:a] + cond[:m.start()] + str(v + 1) + cond[m.end():] + l[b:], fn.name, f"constant {v} -> {v + 1} in a condition in {fn.name}()")
                        break
            else:
                m = re.search(r"\s([+-])\s*1\b", l)
                if m and not _in_string(l, m.start()) and not s.startswith("for"):
                    n = "-" if m.group(1) == "+" else "+"
                    add(i, "arith", l[:m.start(1)] + n + l[m.end(1):], fn.name, f"`{m.group(1)} 1` -> `{n} 1` in {fn.name}()")
    return out


def mutants(rel, text, lang):
    return py_mutants(rel, text) if lang == "py" else c_mutants(rel, text)
