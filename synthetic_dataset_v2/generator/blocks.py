"""Code blocks of the synthetic projects: functions, classes, modules, the clean archetypes and the debt templates.

A project is built from  Fn (function / method), Cls (class), ImportLine and Module objects, so that the history simulator can edit a single
function in place (modify a literal = rework inside the region, or insert a statement = growth of the region) and render the files again.
Placeholders in the templates:  $E entity class name, $e snake case, $rv record variable, $s1 text field, $n1 $n2 numeric fields, $k instance suffix.
A trailing marker (the character U+00A4) on a template line makes that line "tunable": the simulator may change its first integer literal.
"""
import re

TUNE = "¤"
INT = re.compile(r"(?<![\w.'\"%-])(\d+)(?![\w.'\"])")
TIERS = ["platinum", "gold", "silver", "bronze", "basic", "legacy", "trial", "minor", "tiny", "edge", "low", "micro", "base", "alpha", "beta", "gamma", "delta", "omega"]


def snake(s):
    return re.sub(r"(?<!^)(?=[A-Z])", "_", s).lower().replace("__", "_")


def pl(e):
    return e[:-1] + "ies" if e.endswith("y") else e + "es" if e.endswith(("s", "x", "ch", "sh")) else e + "s"


def sub(text, **kw):
    for k in sorted(kw, key=len, reverse=True):
        text = text.replace("$" + k, str(kw[k]))
    return text


def mk(lines, **kw):
    """template lines -> (body, tune indices)"""
    body, tune = [], []
    for l in lines:
        l = sub(l, **kw)
        if l.endswith(TUNE):
            l = l[:-1]
            tune.append(len(body))
        body.append(l)
    return body, tune


def bump(line):
    """change the first integer literal of a line by +1 (None if there is none)."""
    m = INT.search(line)
    if not m:
        return None
    v = int(m.group(1))
    return line[:m.start(1)] + str(v + 1 if v < 900 else v - 1) + line[m.end(1):]


class Fn:
    def __init__(self, name, params, body, tune=(), doc=None, sample=None, tune_sig=False):
        self.name, self.params, self.body, self.tune = name, params, list(body), list(tune)
        self.doc = doc
        self.sample = list(sample or [])        # statements for the smoke test; {m} = this module
        self.tune_sig = tune_sig
        self.sig_edits = 0

    def lines(self, style, indent=""):
        out = [indent + "def %s(%s):" % (self.name, self.params)]
        if style.doc and self.doc:
            out.append(indent + '    """%s"""' % self.doc)
        out += [indent + "    " + b if b else "" for b in self.body]
        return out

    # ---- edits
    def modify(self, rng, k=1):
        """rework inside the function: change the first integer literal of k tunable lines. returns number of lines changed."""
        cand = list(self.tune) + ([-1] if self.tune_sig else [])
        rng.shuffle(cand)
        n = 0
        for i in cand:
            if n >= k:
                break
            if i == -1:
                new = bump(self.params)
                if new and new != self.params:
                    self.params = new
                    n += 1
            else:
                new = bump(self.body[i])
                if new and new != self.body[i]:
                    self.body[i] = new
                    n += 1
        return n

    def grow(self, rng, n=1):
        """insert n statements at the top of the body (growth of the region); n > 1 adds conditions as well (the function can cross a size / complexity threshold)."""
        if n <= 1:
            stmt = "_trace_%d = %d" % (rng.randint(100, 999), rng.randint(1, 9))
            self.body.insert(0, stmt)
            self.tune = [t + 1 for t in self.tune]
            self.padn = getattr(self, "padn", 0) + 1          # the statement is part of the removable top block
            return 1
        pad, tune = pad_lines(rng, n, 900)
        self.body = pad + self.body
        self.tune = tune + [t + len(pad) for t in self.tune]
        self.padn = getattr(self, "padn", 0) + len(pad)
        return n

    def set_body(self, body, tune):
        self.body, self.tune = list(body), list(tune)


class Cls:
    def __init__(self, name, methods, doc=None, bases=""):
        self.name, self.methods, self.doc, self.bases = name, methods, doc, bases

    def lines(self, style, indent=""):
        out = [indent + "class %s%s:" % (self.name, "(%s)" % self.bases if self.bases else "")]
        if style.doc and self.doc:
            out.append(indent + '    """%s"""' % self.doc)
        for i, m in enumerate(self.methods):
            if i:
                out.append("")
            out += m.lines(style, indent + "    ")
        return out

    @property
    def sample(self):
        return [s for m in self.methods for s in m.sample]


class ImportLine:
    def __init__(self, text, comment=""):
        self.text, self.comment, self.ver = text, comment, 0

    def render(self):
        c = self.comment + (" v%d" % self.ver if self.ver else "")
        return self.text + ("  # " + c.strip() if c.strip() else "")


class Module:
    def __init__(self, name, doc):
        self.name, self.doc = name, doc
        self.imports = []          # ImportLine
        self.prelude = []          # raw module-level lines
        self.items = []            # Fn / Cls

    def add_import(self, text, comment=""):
        for i in self.imports:
            if i.text == text:
                return i
        il = ImportLine(text, comment)
        self.imports.append(il)
        return il

    def drop_import(self, il):
        self.imports = [i for i in self.imports if i is not il]

    def render(self, style):
        out = ['"""%s"""' % self.doc, ""]
        std = [i for i in self.imports if not i.text.startswith("from .") and not i.text.startswith("from . ")]
        rel = [i for i in self.imports if i not in std]
        out += [i.render() for i in std]
        if std and rel:
            out.append("")
        out += [i.render() for i in rel]
        if self.imports:
            out.append("")
        if self.prelude:
            out += self.prelude + [""]
        for it in self.items:
            out += ["", ""] + it.lines(style)
        return "\n".join(out).rstrip("\n") + "\n"


class Style:
    """per-project writing habits, so that two projects do not read alike"""
    def __init__(self, rng):
        self.doc = rng.random() < 0.6
        self.rv = rng.choice(["rec", "item", "row", "entry", "data"])
        self.verbs = dict(
            validate=rng.choice(["validate", "check", "verify"]), summarize=rng.choice(["summarize", "aggregate", "tally"]),
            rank=rng.choice(["rank", "top", "order"]), score=rng.choice(["score", "rate", "evaluate"]),
            format=rng.choice(["format", "render", "describe"]), parse=rng.choice(["parse", "load", "decode"]),
            search=rng.choice(["search", "find", "scan"]), notify=rng.choice(["notify", "announce", "alert"]),
            process=rng.choice(["process", "handle", "run"]), next=rng.choice(["next", "pick", "take"]),
        )


class Ent:
    def __init__(self, name, fields):
        self.E, self.e = name, snake(name)
        self.fields = fields
        self.S = [f for f, k in fields if k == "s"]
        self.N = [f for f, k in fields if k == "n"]
        self.B = [f for f, k in fields if k == "b"]
        self.s1, self.n1 = self.S[0], self.N[0]
        self.n2 = self.N[1] if len(self.N) > 1 else self.N[0]
        self.s2 = self.S[1] if len(self.S) > 1 else self.S[0]

    def demo(self):
        parts = []
        for f, k in self.fields:
            parts.append('"%s": %s' % (f, '"x"' if k == "s" else "3" if k == "n" else "True"))
        return "{" + ", ".join(parts) + "}"

    def csv_demo(self):
        return ",".join("x" if k == "s" else "3" if k == "n" else "true" for f, k in self.fields)

    def kw(self, st, k=""):
        return dict(E=self.E, e=self.e, rv=st.rv, s1=self.s1, s2=self.s2, n1=self.n1, n2=self.n2, k=k, fields=", ".join('"%s"' % f for f, _ in self.fields) + ",", nf=len(self.fields))


# ================================================================== clean archetypes
# each returns (module kind, [Fn or Cls])

def a_validate(ent, st, rng):
    kw = ent.kw(st)
    body, tune = mk([
        "errors = []",
        "if not isinstance($rv, dict):",
        '    return ["$e must be a dict"]',
        "for key in ($fields):",
        "    if key not in $rv:",
        '        errors.append("missing " + key)',
        'if len(str($rv.get("$s1", ""))) > 40:' + TUNE,
        '    errors.append("$s1 too long")',
        'if $rv.get("$n1", 0) < 0:',
        '    errors.append("$n1 must not be negative")',
        "return errors"], **kw)
    name = "%s_%s" % (st.verbs["validate"], ent.e)
    return "validators", [Fn(name, st.rv, body, tune, "Return the list of problems of one $e record.".replace("$e", ent.e), ["{m}.%s(%s)" % (name, ent.demo())])]


def a_summarize(ent, st, rng):
    kw = ent.kw(st)
    body, tune = mk([
        "totals = {}",
        "for it in items:",
        '    key = it.get("$s1", "?")',
        '    totals[key] = totals.get(key, 0) + it.get("$n1", 0)',
        "out = []",
        "for key in sorted(totals):",
        "    out.append((key, round(totals[key], 2)))" + TUNE,
        "return out"], **kw)
    name = "%s_%s" % (st.verbs["summarize"], pl(ent.e))
    return "reports", [Fn(name, "items", body, tune, "Total of $n1 per $s1.".replace("$n1", ent.n1).replace("$s1", ent.s1), ["{m}.%s([%s, %s])" % (name, ent.demo(), ent.demo())])]


def a_rank(ent, st, rng):
    kw = ent.kw(st)
    body, tune = mk([
        "if limit <= 0:",
        "    return []",
        'ordered = sorted(items, key=lambda it: it.get("$n1", 0), reverse=True)',
        "return ordered[:limit]"], **kw)
    name = "%s_%s" % (st.verbs["rank"], pl(ent.e))
    return "rules", [Fn(name, "items, limit=10", body, tune, "Best $e records by $n1.".replace("$e", ent.e).replace("$n1", ent.n1), ["{m}.%s([%s])" % (name, ent.demo())], tune_sig=True)]


def a_score(ent, st, rng):
    kw = ent.kw(st)
    body, tune = mk([
        'value = $rv.get("$n1", 0)',
        "if value >= 100:" + TUNE,
        "    bonus = 0.2",
        "elif value >= 50:" + TUNE,
        "    bonus = 0.1",
        "else:",
        "    bonus = 0",
        "return round(value * (1 + bonus), 2)"], **kw)
    name = "%s_%s" % (st.verbs["score"], ent.e)
    return "rules", [Fn(name, st.rv, body, tune, "Score of one $e with a bonus for large values.".replace("$e", ent.e), ["{m}.%s(%s)" % (name, ent.demo())])]


def a_format(ent, st, rng):
    kw = ent.kw(st)
    body, tune = mk([
        'label = str($rv.get("$s1", "")).strip().title()',
        'return "$E: %-20s %8.2f" % (label[:20], $rv.get("$n1", 0))' + TUNE], **kw)
    name = "%s_%s" % (st.verbs["format"], ent.e)
    return "reports", [Fn(name, st.rv, body, tune, "One line of text for a $e.".replace("$e", ent.e), ["{m}.%s(%s)" % (name, ent.demo())])]


def a_parse(ent, st, rng):
    kw = ent.kw(st)
    items = []
    for i, (f, k) in enumerate(ent.fields):
        v = "parts[%d]" % i if k == "s" else "float(parts[%d])" % i if k == "n" else 'parts[%d].lower() == "true"' % i
        items.append('"%s": %s' % (f, v))
    body, tune = mk([
        'parts = [p.strip() for p in line.split(",")]',
        "if len(parts) > 40:" + TUNE,
        '    raise ValueError("too many fields")',
        "return {" + ", ".join(items) + "}"], **kw)
    name = "%s_%s" % (st.verbs["parse"], ent.e)
    return "storage", [Fn(name, "line", body, tune, "Read one $e from a comma separated line.".replace("$e", ent.e), ['{m}.%s("%s")' % (name, ent.csv_demo())])]


def a_store(ent, st, rng):
    cls = ent.E + "Store"
    m_init = Fn("__init__", "self", *mk(["self._items = {}", "self.limit = 1000" + TUNE]), doc=None)
    m_add = Fn("add", "self, key, rec", *mk(["if len(self._items) >= self.limit:", '    raise ValueError("store full")', "self._items[key] = rec"]))
    m_get = Fn("get", "self, key, default=None", *mk(["return self._items.get(key, default)"]))
    m_rem = Fn("remove", "self, key", *mk(["return self._items.pop(key, None)"]))
    m_all = Fn("all", "self", *mk(["return list(self._items.values())"]))
    for m, n in ((m_init, "__init__"),):
        pass
    c = Cls(cls, [m_init, m_add, m_get, m_rem, m_all], "In memory store of $e records.".replace("$e", ent.e))
    c.methods[0].sample = ["_s = {m}.%s()" % cls, '_s.add("k", %s)' % ent.demo(), '_s.get("k")', '_s.all()', '_s.remove("k")']
    return "models", [c]


def a_queue(ent, st, rng):
    kw = ent.kw(st)
    body, tune = mk([
        "if not queue:",
        "    return None",
        "if len(queue) > 500:" + TUNE,
        "    queue[:] = queue[-500:]",
        "best = queue[0]",
        "for job in queue[1:]:",
        '    if job.get("$n1", 0) > best.get("$n1", 0):',
        "        best = job",
        "queue.remove(best)",
        "return best"], **kw)
    name = "%s_%s_job" % (st.verbs["next"], ent.e)
    return "rules", [Fn(name, "queue", body, tune, None, ["{m}.%s([%s, %s])" % (name, ent.demo(), ent.demo())])]


def a_lookup(ent, st, rng):
    body, tune = mk([
        "hit = cache.get(key)",
        "if hit is None:",
        "    return None",
        "value, stamp = hit",
        "if now - stamp > ttl:",
        "    del cache[key]",
        "    return None",
        "return value"])
    name = "lookup_%s" % ent.e
    return "utils", [Fn(name, "cache, key, now, ttl=60", body, tune, None, ["{m}.%s({}, 'k', 5)" % name], tune_sig=True)]


def a_search(ent, st, rng):
    kw = ent.kw(st)
    body, tune = mk([
        "term = term.lower()",
        "hits = []",
        "for it in items:",
        '    text = str(it.get("$s1", "")).lower()',
        "    if term in text:",
        "        score = 1 + text.count(term)" + TUNE,
        "        hits.append((score, it))",
        "hits.sort(key=lambda p: -p[0])",
        "return [h[1] for h in hits]"], **kw)
    name = "%s_%s" % (st.verbs["search"], pl(ent.e))
    return "storage", [Fn(name, "items, term", body, tune, None, ["{m}.%s([%s], 'x')" % (name, ent.demo())])]


def a_notify(ent, st, rng):
    kw = ent.kw(st)
    body, tune = mk([
        'subject = "$E update: " + str($rv.get("$s1", ""))',
        'if channel == "mail":',
        '    body = "Dear user, %s was updated." % subject',
        "else:",
        "    body = subject[:60]" + TUNE,
        'return {"channel": channel, "subject": subject, "body": body}'], **kw)
    name = "%s_%s" % (st.verbs["notify"], ent.e)
    return "services", [Fn(name, '%s, channel="mail"' % st.rv, body, tune, None, ["{m}.%s(%s)" % (name, ent.demo())])]


def a_process(ent, st, rng, have):
    """workflow: validates, scores and formats one record by calling functions of the lower layers (creates the import edges of the layering).
    The calls are module qualified (from . import validators; validators.f(...)), so that a later import cycle between two modules stays importable."""
    v = "%s_%s" % (st.verbs["validate"], ent.e)
    sc = "%s_%s" % (st.verbs["score"], ent.e)
    f = "%s_%s" % (st.verbs["format"], ent.e)
    lines, imports = [], []
    if v in have:
        imports.append((have[v], v))
        lines += ["errors = %s.%s(%s)" % (have[v], v, st.rv), "if errors:", '    return {"ok": False, "errors": errors}']
    else:
        lines += ["errors = []"]
    if sc in have:
        imports.append((have[sc], sc))
        lines += ["value = %s.%s(%s)" % (have[sc], sc, st.rv)]
    else:
        lines += ['value = %s.get("%s", 0)' % (st.rv, ent.n1)]
    if f in have:
        imports.append((have[f], f))
        lines += ["text = %s.%s(%s)" % (have[f], f, st.rv)]
    else:
        lines += ['text = str(%s.get("%s", ""))' % (st.rv, ent.s1)]
    lines += ["if value > 1000:" + TUNE, "    value = 1000", 'return {"ok": True, "value": value, "text": text}']
    body, tune = mk(lines)
    name = "%s_%s" % (st.verbs["process"], ent.e)
    return "services", [Fn(name, st.rv, body, tune, "Check, score and format one $e.".replace("$e", ent.e), ["{m}.%s(%s)" % (name, ent.demo())])], imports


def a_retry():
    body, tune = mk([
        "last = None",
        "for _ in range(attempts):",
        "    try:",
        "        return fn()",
        "    except Exception as exc:",
        "        last = exc",
        "raise last"])
    return "utils", [Fn("retry", "fn, attempts=3", body, tune, None, ["{m}.retry(lambda: 1)"], tune_sig=True)]


ARCHETYPES = [a_validate, a_summarize, a_rank, a_score, a_format, a_parse, a_store, a_queue, a_lookup, a_search, a_notify]


# ---------------------------------------------------------------- v2: function sizes follow the real log-normal law
import math as _math


def pad_lines(rng, n, start=100):
    """n harmless statements (an assignment, a condition and its body, an assignment) with the indices of the tunable ones"""
    pad, tune, k = [], [], rng.randint(start, start + 799)
    while len(pad) < n:
        v = "_p%d" % (len(pad) + k)
        tune.append(len(pad)); pad.append("%s = %d + len(str(%d))" % (v, rng.randint(2, 9), rng.randint(1, 9)))
        if len(pad) < n:
            pad.append("if %s > %d:" % (v, rng.randint(1, 20)))
        if len(pad) < n:
            tune.append(len(pad)); pad.append("    %s -= %d" % (v, rng.randint(1, 9)))
    while pad and pad[-1].startswith("if "):          # never end on a condition without its body
        pad.pop()
    tune = [t for t in tune if t < len(pad)]
    return pad, tune


def pad_function(fn, rng, mu=2.0, sigma=1.4, cap=260):
    """lengthen a clean function with harmless statements (some tunable, some conditional) so that its size follows a log-normal law and its complexity grows with its size;
    every function gets at least one tunable line, so that every function can be edited"""
    target = int(min(cap, max(4, rng.lognormvariate(mu, sigma))))
    have = len(fn.body) + 1
    n = max(target - have, 0 if fn.tune else 2)
    if n <= 0:
        return
    pad, tune = pad_lines(rng, n)
    fn.body = pad + fn.body
    fn.tune = tune + [t + len(pad) for t in fn.tune]
    fn.padn = len(pad)
