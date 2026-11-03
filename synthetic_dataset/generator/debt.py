"""Debt templates. Each template builds the code of ONE debt instance and a clean variant that replaces it when the debt is repaid.
types: complexity, concurrency, security, coupling_cohesion (the fifth, dependency_structure, is built in simulate.py because it edits imports)."""
from blocks import Cls, Fn, TIERS, TUNE, mk, sub


class Spec:
    def __init__(self, ptype, template, granularity, mod_kind, units, prelude=(), imports=(), clean=None, region="function"):
        self.ptype, self.template, self.granularity, self.mod_kind = ptype, template, granularity, mod_kind
        self.units, self.prelude, self.imports = units, list(prelude), list(imports)
        self.clean = clean or {}            # unit index -> (body, tune) of the repaired version
        self.region = region                # function | class


# ------------------------------------------------------------------ complexity
def c_ladder(ent, st, rng, k):
    n = rng.randint(11, 16)
    labels = rng.sample(TIERS, min(n, len(TIERS)))
    lines = ['v = $rv.get("$n1", 0)', 'w = $rv.get("$n2", 0)']
    top = rng.randint(80, 95)
    for i in range(n):
        thr = max(top - 6 * i, 1)
        var = "v" if i % 3 != 2 else "w"
        lines += [("if" if i == 0 else "elif") + " %s > %d:" % (var, thr) + TUNE, '    tier = "%s"' % labels[i]]
    lines += ["else:", '    tier = "none"', 'if $rv.get("$s1") and tier != "none":', '    tier = tier + "*"', "return tier"]
    body, tune = mk(lines, **ent.kw(st, k))
    name = "classify_%s_%s" % (ent.e, k)
    cb = mk(['v = $rv.get("$n1", 0)', "for limit, name in ((90, \"platinum\"), (50, \"basic\")):" + TUNE, "    if v > limit:", "        return name", 'return "none"'], **ent.kw(st, k))
    return Spec("complexity", "ladder", "function", "rules", [Fn(name, st.rv, body, tune, None, ["{m}.%s(%s)" % (name, ent.demo())])], clean={0: cb})


def c_nested(ent, st, rng, k):
    lines = [
        "flags = flags or {}", "result = None", "if $rv:", '    if $rv.get("$s1"):', '        if $rv.get("$n1", 0) > 0:' + TUNE,
        '            if flags.get("strict"):', '                if $rv.get("$n2", 0) > 10:' + TUNE, '                    if flags.get("audit"):',
        '                        result = "audited"', "                    else:", '                        result = "strict"',
        "                else:", '                    result = "short"', "            else:", '                result = "ok"',
        "        else:", '            result = "empty"', "    else:", '        result = "unnamed"', "else:", '    result = "missing"',
        'for key in ("a", "b", "c", "d"):', '    if flags.get(key) and result:', "        result = result + key",
        'while result and len(result) > 12:' + TUNE, "    result = result[:-1]",
        'if result == "ok" and flags.get("a") or result == "strict" and flags.get("b"):', '    result = result.upper()', "return result"]
    body, tune = mk(lines, **ent.kw(st, k))
    name = "handle_%s_%s" % (ent.e, k)
    cb = mk(['return "ok" if $rv else "missing"'], **ent.kw(st, k))
    return Spec("complexity", "nested", "function", "rules", [Fn(name, st.rv + ", flags=None", body, tune, None, ["{m}.%s(%s)" % (name, ent.demo())])], clean={0: cb})


def c_params(ent, st, rng, k):
    n = rng.randint(7, 9)
    names = ["a", "b", "c", "d", "e_", "f_", "g_", "h_", "i_"][:n]
    flags = ["flag_x=False", "flag_y=False", "flag_z=True", "scale=5"]
    params = "name, kind, " + ", ".join(names[:4]) + ", " + ", ".join(flags)
    body, tune = mk([
        'out = {"name": name, "kind": kind}', 'out["total"] = a + b + c + d', "if flag_x:", '    out["total"] = out["total"] * 2' + TUNE,
        "if flag_y:", '    out["note"] = "flagged"', "if flag_z:", '    out["total"] = round(out["total"], 1)', 'out["scaled"] = out["total"] * scale', "return out"])
    name = "build_%s_%s" % (ent.e, k)
    cb = mk(['return {"name": name, "kind": kind, "total": a + b + c + d}' + TUNE])
    return Spec("complexity", "params", "function", "rules", [Fn(name, params, body, tune, None, ["{m}.%s('n', 'k', 1, 2, 3, 4)" % name], tune_sig=True)], clean={0: cb})


def c_long(ent, st, rng, k):
    lines = ["lines = []", 'lines.append("== $E report ==")', "count = len(items)", 'lines.append("count: %d" % count)']
    for i in range(rng.randint(8, 11)):
        fld = ent.N[i % len(ent.N)]
        lines += ["total_%d = 0" % i, "for it in items:", '    total_%d += it.get("%s", 0)' % (i, fld),
                  "avg_%d = total_%d / count if count else 0" % (i, i), "width_%d = %d" % (i, 8 + i) + TUNE,
                  'lines.append("%s: %%*.2f" %% (width_%d, avg_%d))' % (fld[:10], i, i)]
    lines += ['return "\\n".join(lines)']
    body, tune = mk(lines, **ent.kw(st, k))
    name = "report_%s_%s" % (ent.e, k)
    cb = mk(['return "== $E report ==\\n" + str(len(items))' + TUNE], **ent.kw(st, k))
    return Spec("complexity", "long", "function", "reports", [Fn(name, "items", body, tune, None, ["{m}.%s([%s])" % (name, ent.demo())])], clean={0: cb})


# ------------------------------------------------------------------ concurrency
def k_counter(ent, st, rng, k):
    bump_name, run_name = "bump_%s_counter_%s" % (ent.e, k), "run_%s_workers_%s" % (ent.e, k)
    kw = dict(k=k)
    b, t = mk(["current = _COUNTER_$k[\"value\"]", "time.sleep(0)", '_COUNTER_$k["value"] = current + 1' + TUNE, 'return _COUNTER_$k["value"]'], **kw)
    rb, rt = mk(["threads = [threading.Thread(target=%s) for _ in range(workers)]" % bump_name, "for t in threads:", "    t.start()", "for t in threads:", "    t.join()", 'return _COUNTER_$k["value"]'], **kw)
    cb = mk(["with _LOCK_$k:", '    current = _COUNTER_$k["value"]', "    time.sleep(0)", '    _COUNTER_$k["value"] = current + 1' + TUNE, '    return _COUNTER_$k["value"]'], **kw)
    u = [Fn(bump_name, "", b, t, None, ["{m}.%s()" % bump_name]), Fn(run_name, "workers=4", rb, rt, None, ["{m}.%s()" % run_name], tune_sig=True)]
    return Spec("concurrency", "unlocked_counter", "function", "services", u, ['_COUNTER_%s = {"value": 0}' % k, "_LOCK_%s = threading.Lock()" % k], ["import threading", "import time"], {0: cb})


def k_check_act(ent, st, rng, k):
    g, w = "get_or_build_%s_%s" % (ent.e, k), "warm_%s_cache_%s" % (ent.e, k)
    b, t = mk(["if key not in _CACHE_$k:", "    time.sleep(0)", '    _CACHE_$k[key] = {"key": key, "built": len(_CACHE_$k) + 1}' + TUNE, "return _CACHE_$k[key]"], k=k)
    rb, rt = mk(["threads = [threading.Thread(target=%s, args=(key,)) for key in keys]" % g, "for t in threads[:workers]:", "    t.start()", "for t in threads[:workers]:", "    t.join()", "return len(_CACHE_$k)"], k=k)
    cb = mk(["with _LOCK_$k:", "    if key not in _CACHE_$k:", '        _CACHE_$k[key] = {"key": key, "built": len(_CACHE_$k) + 1}' + TUNE, "    return _CACHE_$k[key]"], k=k)
    u = [Fn(g, "key", b, t, None, ['{m}.%s("a")' % g]), Fn(w, "keys, workers=4", rb, rt, None, ['{m}.%s(["a", "b"])' % w], tune_sig=True)]
    return Spec("concurrency", "check_then_act", "function", "services", u, ["_CACHE_%s = {}" % k, "_LOCK_%s = threading.Lock()" % k], ["import threading", "import time"], {0: cb})


def k_lock_order(ent, st, rng, k):
    a, b_ = "transfer_%s_in_%s" % (ent.e, k), "transfer_%s_out_%s" % (ent.e, k)
    b1, t1 = mk(["with _LOCK_A_$k:", "    time.sleep(0)", "    with _LOCK_B_$k:", "        return n + 1" + TUNE], k=k)
    b2, t2 = mk(["with _LOCK_B_$k:", "    time.sleep(0)", "    with _LOCK_A_$k:", "        return n - 1" + TUNE], k=k)
    cb2 = mk(["with _LOCK_A_$k:", "    time.sleep(0)", "    with _LOCK_B_$k:", "        return n - 1" + TUNE], k=k)
    u = [Fn(a, "n", b1, t1, None, ["{m}.%s(1)" % a]), Fn(b_, "n", b2, t2, None, ["{m}.%s(1)" % b_])]
    return Spec("concurrency", "lock_order", "function", "services", u, ["_LOCK_A_%s = threading.Lock()" % k, "_LOCK_B_%s = threading.Lock()" % k], ["import threading", "import time"], {1: cb2})


def k_no_release(ent, st, rng, k):
    n = "update_%s_total_%s" % (ent.e, k)
    b, t = mk(["_LOCK_$k.acquire()", "total = 0", "for v in values:", "    total += int(v)" + TUNE, "_LOCK_$k.release()", "return total"], k=k)
    cb = mk(["total = 0", "with _LOCK_$k:", "    for v in values:", "        total += int(v)" + TUNE, "return total"], k=k)
    return Spec("concurrency", "lock_not_released", "function", "services", [Fn(n, "values", b, t, None, ['{m}.%s(["1", "2"])' % n])], ["_LOCK_%s = threading.Lock()" % k], ["import threading"], {0: cb})


def k_shared_list(ent, st, rng, k):
    r, d = "record_%s_%s" % (ent.e, k), "drain_%s_%s" % (ent.e, k)
    b1, t1 = mk(["_LOG_$k.append(msg)", "if len(_LOG_$k) > 100:" + TUNE, "    del _LOG_$k[0]"], k=k)
    b2, t2 = mk(["items = list(_LOG_$k)", "_LOG_$k.clear()", "return items"], k=k)
    cb1 = mk(["with _LOCK_$k:", "    _LOG_$k.append(msg)", "    if len(_LOG_$k) > 100:" + TUNE, "        del _LOG_$k[0]"], k=k)
    u = [Fn(r, "msg", b1, t1, None, ['{m}.%s("m")' % r]), Fn(d, "", b2, t2, None, ["{m}.%s()" % d])]
    return Spec("concurrency", "shared_list", "function", "services", u, ["_LOG_%s = []" % k, "_LOCK_%s = threading.Lock()" % k], ["import threading"], {0: cb1})


# ------------------------------------------------------------------ security
def s_sql(ent, st, rng, k):
    n = "find_%s_by_%s_%s" % (ent.e, ent.s1, k)
    b, t = mk(["conn = sqlite3.connect(\":memory:\")", 'conn.execute("CREATE TABLE t ($s1 TEXT, $n1 REAL)")', "conn.execute(\"INSERT INTO t VALUES ('seed', 1)\")" + TUNE,
               "query = \"SELECT * FROM t WHERE $s1 = '%s'\" % value", "rows = conn.execute(query).fetchall()", "conn.close()", "return rows"], **ent.kw(st, k))
    cb = mk(["conn = sqlite3.connect(\":memory:\")", 'conn.execute("CREATE TABLE t ($s1 TEXT, $n1 REAL)")', "conn.execute(\"INSERT INTO t VALUES ('seed', 1)\")" + TUNE,
             'rows = conn.execute("SELECT * FROM t WHERE $s1 = ?", (value,)).fetchall()', "conn.close()", "return rows"], **ent.kw(st, k))
    return Spec("security", "sql_injection", "function", "storage", [Fn(n, "value", b, t, None, ['{m}.%s("a")' % n])], [], ["import sqlite3"], {0: cb})


def s_shell(ent, st, rng, k):
    n = "archive_%s_%s" % (ent.e, k)
    b, t = mk(['cmd = "echo archiving " + name', "out = subprocess.run(cmd, shell=True, capture_output=True, text=True)", "return out.stdout.strip()[:80]" + TUNE])
    cb = mk(['out = subprocess.run(["echo", "archiving", str(name)], capture_output=True, text=True)', "return out.stdout.strip()[:80]" + TUNE])
    return Spec("security", "shell_injection", "function", "services", [Fn(n, "name", b, t, None, ['{m}.%s("a")' % n])], [], ["import subprocess"], {0: cb})


def s_eval(ent, st, rng, k):
    n = "compute_%s_expr_%s" % (ent.e, k)
    b, t = mk(["limit = 100" + TUNE, "if len(expr) > limit:", '    raise ValueError("expression too long")', 'allowed = {"abs": abs, "min": min, "max": max}', 'return eval(expr, {"__builtins__": {}}, allowed)'])
    cb = mk(["limit = 100" + TUNE, "if len(expr) > limit:", '    raise ValueError("expression too long")', "return float(expr)"])
    return Spec("security", "eval_input", "function", "services", [Fn(n, "expr", b, t, None, ['{m}.%s("1+1")' % n])], [], [], {0: cb})


def s_weak_hash(ent, st, rng, k):
    n = "sign_%s_%s" % (ent.e, k)
    b, t = mk(["digest = hashlib.md5((SECRET_$k + str(payload)).encode()).hexdigest()", "return digest[:16]" + TUNE], k=k)
    cb = mk(["digest = hmac.new(os.environ.get(\"SECRET_KEY\", \"x\").encode(), str(payload).encode(), hashlib.sha256).hexdigest()", "return digest[:16]" + TUNE])
    return Spec("security", "weak_hash_secret", "function", "services", [Fn(n, "payload", b, t, None, ['{m}.%s("a")' % n])], ['SECRET_%s = "change-me-%s"' % (k, 100 + int(k))], ["import hashlib", "import hmac", "import os"], {0: cb})


def s_token(ent, st, rng, k):
    n = "new_%s_token_%s" % (ent.e, k)
    b, t = mk(['return "".join(random.choice("abcdef0123456789") for _ in range(12))' + TUNE])
    cb = mk(["return secrets.token_hex(6)" + TUNE])
    return Spec("security", "insecure_random", "function", "services", [Fn(n, "", b, t, None, ["{m}.%s()" % n])], [], ["import random", "import secrets"], {0: cb})


def s_path(ent, st, rng, k):
    n = "read_%s_file_%s" % (ent.e, k)
    b, t = mk(["path = os.path.join(BASE_DIR_$k, name)", "if not os.path.exists(path):", '    return ""', "with open(path) as fh:", "    return fh.read(200)" + TUNE], k=k)
    cb = mk(["path = os.path.join(BASE_DIR_$k, os.path.basename(name))", "if not os.path.exists(path):", '    return ""', "with open(path) as fh:", "    return fh.read(200)" + TUNE], k=k)
    return Spec("security", "path_traversal", "function", "storage", [Fn(n, "name", b, t, None, ['{m}.%s("__init__.py")' % n])], ["BASE_DIR_%s = os.path.dirname(__file__)" % k], ["import os"], {0: cb})


def s_pickle(ent, st, rng, k):
    n = "load_%s_blob_%s" % (ent.e, k)
    b, t = mk(["data = pickle.loads(blob)", "if not isinstance(data, dict):", "    return {}", "return {key: data[key] for key in list(data)[:20]}" + TUNE])
    cb = mk(["data = json.loads(blob)", "if not isinstance(data, dict):", "    return {}", "return {key: data[key] for key in list(data)[:20]}" + TUNE])
    return Spec("security", "unsafe_deserialize", "function", "storage", [Fn(n, "blob", b, t, None, ['{m}.%s(__import__("pickle").dumps({"a": 1}))' % n])], [], ["import pickle", "import json"], {0: cb})


# ------------------------------------------------------------------ coupling / cohesion
def p_envy(ent, st, rng, k):
    n = "summary_%s_%s" % (ent.e, k)
    b, t = mk(['head = str(src.$s1).strip().title()', 'body = str(src.$n1) + "/" + str(src.$n2)', "tail = str(src.$s1)[:3] + str(src.$n1)", "code = src.$n1 * 3 + src.$n2 * 2" + TUNE,
               "flag = bool(src.$n2) and bool(src.$s1)", 'return "%s %s %s %s %s" % (head, body, tail, code, flag)'], **ent.kw(st, k))
    cb = mk(['return "%s" % (src.$s1,)'], **ent.kw(st, k))
    sample = ["{m}.%s(__import__(\"types\").SimpleNamespace(**%s))" % (n, ent.demo())]
    return Spec("coupling_cohesion", "feature_envy", "function", "services", [Fn(n, "src", b, t, None, sample)], clean={0: cb})


def p_god_class(ent, st, rng, k):
    cname = "%sManager%s" % (ent.E, k)
    M = []
    M.append(Fn("__init__", "self", *mk(["self.rows = []", "self.cache = {}", "self.sent = 0", "self.limit = 50" + TUNE])))
    M.append(Fn("add_row", "self, row", *mk(["self.rows.append(row)"])))
    M.append(Fn("check_row", "self, row", *mk(["return bool(row)"])))
    M.append(Fn("format_row", "self, row", *mk(["return str(row)[:40]" + TUNE])))
    M.append(Fn("send_row", "self, row", *mk(["self.sent += 1", "return self.sent"])))
    M.append(Fn("cache_row", "self, key, row", *mk(["self.cache[key] = row"])))
    M.append(Fn("total_rows", "self", *mk(["return len(self.rows)"])))
    M.append(Fn("drop_cache", "self", *mk(["self.cache.clear()"])))
    M.append(Fn("export_rows", "self", *mk(["return [str(r) for r in self.rows][:self.limit]"])))
    M[0].sample = ["_g = {m}.%s()" % cname, '_g.add_row("r")', '_g.check_row("r")', '_g.format_row("r")', '_g.send_row("r")', '_g.cache_row("k", "r")', "_g.total_rows()", "_g.drop_cache()", "_g.export_rows()"]
    c = Cls(cname, M, "Everything about %s records in one place." % ent.e)
    return Spec("coupling_cohesion", "god_class", "class", "services", [c], clean={}, region="class")


def p_chain(ent, st, rng, k):
    n = "locate_%s_%s" % (ent.e, k)
    b, t = mk(["limit = 30" + TUNE, "return str(root.org.team.owner.contact.name)[:limit]"])
    cb = mk(["limit = 30" + TUNE, "return str(root)[:limit]"])
    sample = ['{m}.%s(__import__("types").SimpleNamespace(org=__import__("types").SimpleNamespace(team=__import__("types").SimpleNamespace(owner=__import__("types").SimpleNamespace(contact=__import__("types").SimpleNamespace(name="x"))))))' % n]
    return Spec("coupling_cohesion", "message_chain", "function", "rules", [Fn(n, "root", b, t, None, sample)], clean={0: cb})


def p_intimacy(ent, st, rng, k):
    n = "reset_%s_store_%s" % (ent.e, k)
    b, t = mk(["store._items.clear()", 'store._items["seed"] = {"$s1": "seed", "$n1": 0}' + TUNE, "return len(store._items)"], **ent.kw(st, k))
    cb = mk(['store.add("seed", {"$s1": "seed", "$n1": 0})' + TUNE, "return len(store.all())"], **ent.kw(st, k))
    sample = ['{m}.%s(mods["models"].%sStore())' % (n, ent.E)]
    return Spec("coupling_cohesion", "private_access", "function", "services", [Fn(n, "store", b, t, None, sample)], clean={0: cb})


TEMPLATES = {
    "complexity": [c_ladder, c_nested, c_params, c_long],
    "concurrency": [k_counter, k_check_act, k_lock_order, k_no_release, k_shared_list],
    "security": [s_sql, s_shell, s_eval, s_weak_hash, s_token, s_path, s_pickle],
    "coupling_cohesion": [p_envy, p_god_class, p_chain, p_intimacy],
}
