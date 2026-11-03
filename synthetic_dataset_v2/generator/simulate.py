"""Build one synthetic project and its git history.

 - the code base is assembled from archetype functions (blocks.py) in a layered package;
 - debt instances (debt.py, plus the dependency templates below) are introduced at scheduled releases, and repaid at random;
 - every release has an activity level (the 'release clock'); every function and every debt instance has a latent edit rate;
   an edit changes a literal inside the function (rework inside the region = interest) or adds a statement (growth of the region);
 - everything is committed to git with dates, authors, messages and a tag per release.
The latent rates and regimes are written to the manifest: they are the generator's ground truth, not something a method may see.
"""
import json
import math
import os
import random
import shutil
import subprocess
import tempfile
from collections import OrderedDict, defaultdict
from datetime import datetime, timedelta, timezone

import blocks as B
import debt as D
from blocks import Cls, Ent, Fn, ImportLine, Module, Style

TIER = {  # entities, releases, modules style, initial share of (archetype x entity) combinations, features per release, major instances
    "S": dict(n_ent=2, rel=(5, 6), init=0.55, feat=0.09, major=(5, 6)),
    "M": dict(n_ent=3, rel=(10, 15), init=0.55, feat=0.25, major=(5, 8)),
    "L": dict(n_ent=4, rel=(20, 30), init=0.6, feat=0.42, major=(7, 10)),
    "X": dict(n_ent=5, rel=(25, 30), init=0.6, feat=0.87, major=(8, 10)),
    "H": dict(n_ent=9, rel=(20, 30), init=0.9, feat=1.74, major=(8, 10)),
}
SUPPORT = [("User", [("name", "s"), ("email", "s"), ("age", "n"), ("active", "b")]), ("AuditEntry", [("action", "s"), ("target", "s"), ("ts", "n"), ("ok", "b")]),
           ("Setting", [("key", "s"), ("value", "s"), ("version", "n")]), ("Notification", [("channel", "s"), ("text", "s"), ("sent", "n"), ("read", "b")])]
REGIMES = {  # frozen share (same for debt and clean code: no avoidance), multiplier of the debt rate, clock autocorrelation (log scale), self-exciting decay, file contagion
    "baseline": dict(pf_d=0.12, pf_c=0.12, dmult=1.0, rho=0.0, decay=False, contagion=False),
    "sticky": dict(pf_d=0.05, pf_c=0.22, dmult=5.0, rho=0.0, decay=False, contagion=False),
    "ar_clock": dict(pf_d=0.22, pf_c=0.22, dmult=1.0, rho=0.9, decay=False, contagion=False),
    "decay": dict(pf_d=0.22, pf_c=0.22, dmult=1.0, rho=0.0, decay=True, contagion=False),
    "contagion": dict(pf_d=0.22, pf_c=0.22, dmult=1.0, rho=0.0, decay=False, contagion=True),
}
# edit-rate law measured on 33 real repositories: P(edit) = 1 - exp(-lambda), lambda = K * lines^GAMMA * heterogeneity (gamma, shape SHAPE), a share of units frozen
LAW = dict(K=float(os.environ.get("SYN_K", 0.0165)), GAMMA=float(os.environ.get("SYN_GAMMA", 0.70)), SHAPE=float(os.environ.get("SYN_SHAPE", 0.72)))
AUTHORS = [("Asha Rao", "asha@example.org"), ("Liam Chen", "liam@example.org"), ("Marta Silva", "marta@example.org"), ("Omar Haddad", "omar@example.org")]
NOUNS = ["helper", "handler", "export", "checker", "adapter", "routine", "utility", "hook", "report", "task"]
MSG_MOD = ["tune limits in {m}", "fix off-by-one in {f}", "adjust defaults for {e}", "update thresholds in {m}", "rework {f}", "small fix in {f}", "tweak {m}"]
MSG_GROW = ["handle one more case in {f}", "extend {f}", "add guard to {f}"]
MSG_REPAY = ["refactor {f}", "simplify {f}", "clean up {m}"]


def gamma_rate(rng, mean, shape=1.5):
    return rng.gammavariate(shape, mean / shape)


def unit_rate(rng, lines, pf, mult=1.0):
    """latent edit rate of a function or instance of `lines` source lines: frozen with probability pf, else K lines^GAMMA times a gamma heterogeneity of mean 1/(1-pf)"""
    if rng.random() < pf:
        return 0.0
    return mult * LAW["K"] * (max(lines, 2) ** LAW["GAMMA"]) * rng.gammavariate(LAW["SHAPE"], 1.0 / LAW["SHAPE"]) / (1 - pf)


class Instance:
    def __init__(self, iid, spec, ent, intro_rel):
        self.id, self.spec, self.ent, self.intro_rel = iid, spec, ent, intro_rel
        self.ptype, self.template, self.granularity = spec.ptype, spec.template, spec.granularity
        self.repaid_rel = None
        self.rate, self.frozen = 0.0, False
        self.module = None
        self.region_kind = spec.region
        self.stmt = None            # import statement text (dependency regions)
        self.import_line = None
        self.removable = []         # (module, ImportLine) added by the instance
        self.units = []
        self.intro_commit = None
        self.mixed = False
        self.edits = []             # (release, kind, lines)


class Project:
    def __init__(self, dom, seed, regime, tier=None):
        self.dom, self.seed, self.regime = dom, seed, regime
        self.tier = tier or dom["tier"]
        self.rng = random.Random(seed)
        self.P = TIER[self.tier]
        self.R = self.rng.randint(*self.P["rel"])
        self.st = Style(self.rng)
        self.pkg = dom["slug"].replace("-", "_")
        self.rp = REGIMES[regime]
        self.mods = OrderedDict()
        self.kinds = defaultdict(list)       # module kind -> module names
        self.layer = {}
        self.names = set()
        self.units = []                      # all Fn (clean + debt) with .rate
        self.instances = []
        self.pairs_used = set()
        self.dirty = set()
        self.combos_left = []
        self.have = {}                       # function name -> module (for workflows)
        self.counter = 0
        ents = list(dom["entities"])
        i = 0
        while len(ents) < self.P["n_ent"]:
            ents.append(SUPPORT[i % len(SUPPORT)])
            i += 1
        self.ents = [Ent(n, f) for n, f in ents[:max(self.P["n_ent"], len(dom["entities"]))]]
        self._modules()

    # ------------------------------------------------------------ structure
    def _add_mod(self, name, doc, layer, kinds=()):
        m = Module(name, doc)
        self.mods[name] = m
        self.layer[name] = layer
        for k in kinds:
            self.kinds[k].append(name)
        self.dirty.add(name)
        return m

    def _modules(self):
        t, title = self.tier, self.dom["title"]
        if t == "S":
            self._add_mod("models", "Data holders of %s." % title, 1, ["models"])
            self._add_mod("core", "Core rules of %s." % title, 2, ["validators", "rules", "reports", "storage", "utils"])
            self._add_mod("services", "Workflows of %s." % title, 3, ["services"])
            self._add_mod("cli", "Command line entry of %s." % title, 4, [])
        else:
            self._add_mod("utils", "Small helpers.", 0, ["utils"])
            self._add_mod("models", "Data holders of %s." % title, 1, ["models"])
            self._add_mod("validators", "Input checks.", 2, ["validators"])
            self._add_mod("rules", "Business rules.", 3, ["rules"] + ([] if t != "M" else ["reports"]))
            self._add_mod("storage", "Parsing and lookup.", 3, ["storage"])
            if t in ("L", "X", "H"):
                self._add_mod("config", "Settings.", 0, [])
                self._add_mod("reports", "Reports and formatting.", 4, ["reports"])
                self._add_mod("events", "Notifications.", 4, [])
                for e in self.ents:
                    self._add_mod("svc_" + e.e, "Workflows of %s." % e.e, 5, ["services"])
            self._add_mod("services", "Workflows of %s." % title, 6, ["services"])
            if t in ("X", "H"):
                for i in range(self.rng.randint(12, 18) if t == "X" else self.rng.randint(30, 42)):
                    self._add_mod("feat_%02d" % (i + 1), "Feature module %d." % (i + 1), 5, ["rules", "storage", "reports"])
            self._add_mod("cli", "Command line entry of %s." % title, 7, [])
        self.mods["cli"].add_import("from . import services")
        self.mods["cli"].items.append(Fn("main", "argv=None", *B.mk(["argv = argv or []", 'print("%s ready (%%d args)" %% len(argv))' % self.pkg, "return 0"]), None, ["{m}.main([])"]))

    def uname(self, base):
        n, i = base, 1
        while n in self.names:
            i += 1
            n = "%s_v%d" % (base, i)
        self.names.add(n)
        return n

    def pick_mod(self, kind):
        return self.rng.choice(self.kinds[kind]) if kind in self.kinds and self.kinds[kind] else self.rng.choice(list(self.mods)[:-1])

    # ------------------------------------------------------------ adding code
    def _register(self, fn, mod, inst=None, rel=1):
        fn.mod, fn.inst, fn.created = mod, inst, rel
        fn.was_debt = inst is not None
        if not (fn.tune or fn.tune_sig):
            fn.rate = 0.0
        elif inst is None:
            fn.rate = unit_rate(self.rng, len(fn.body) + 1, self.rp["pf_c"])
        self.units.append(fn)

    def add_items(self, mod, items, inst=None, rel=1):
        m = self.mods[mod]
        for it in items:
            if isinstance(it, Cls):
                for f in it.methods:
                    self._register(f, mod, inst, rel)
            else:
                self._register(it, mod, inst, rel)
                self.have[it.name] = mod
            m.items.append(it)
        self.dirty.add(mod)

    def add_clean(self, archetype, ent, rel=1):
        res = archetype(ent, self.st, self.rng)
        kind, items = res[0], res[1]
        mod = self.pick_mod(kind)
        for it in items:
            if isinstance(it, Fn):
                B.pad_function(it, self.rng)
                new = self.uname(it.name)
                if new != it.name:
                    it.sample = [s.replace(it.name + "(", new + "(") for s in it.sample]
                    it.name = new
            elif isinstance(it, Cls):
                base = it.name
                if base in self.names:
                    continue
                self.names.add(base)
        self.add_items(mod, items, None, rel)
        for it in items:
            if isinstance(it, Fn):
                self.have[it.name] = mod
        return mod, items

    def _imports_for_workflows(self):
        # services import the functions they call (layering edges high -> low)
        for e in self.ents:
            self.add_workflow(e)

    def add_workflow(self, ent, rel=1):
        mod_kind = "services"
        res = B.a_process(ent, self.st, self.rng, self.have)
        kind, items, imps = res
        mod = ("svc_" + ent.e) if ("svc_" + ent.e) in self.mods else self.pick_mod("services")
        for it in items:
            it.name = self.uname(it.name)
        for m_, fname in imps:
            if m_ != mod:
                self.mods[mod].add_import("from . import %s" % m_)
        self.add_items(mod, items, None, rel)
        self.dirty.add(mod)
        return mod

    def build_initial(self):
        rng = self.rng
        combos = [(a, e) for e in self.ents for a in B.ARCHETYPES]
        rng.shuffle(combos)
        n_init = max(6, int(len(combos) * self.P["init"]))
        for a, e in combos[:n_init]:
            self.add_clean(a, e)
        self.combos_left = combos[n_init:]
        # utility helper
        kind, items = B.a_retry()
        items[0].name = self.uname(items[0].name)
        self.add_items(self.pick_mod("utils"), items)
        for e in self.ents:
            self.add_workflow(e)
        if "services" in self.mods and self.tier in ("L", "X", "H"):
            for e in self.ents:
                self.mods["services"].add_import("from . import svc_%s" % e.e)
        if self.tier in ("X", "H"):
            for n in self.mods:
                if n.startswith("feat_"):
                    self.mods["services"].add_import("from . import %s" % n)
        if "config" in self.mods:
            self.mods["config"].prelude += ['APP_NAME = "%s"' % self.pkg, "DEBUG = False", "TIMEOUT = 30"]
        if "events" in self.mods:
            self.mods["events"].items.append(Fn("emit", "kind, payload", *B.mk(["return {\"kind\": kind, \"payload\": payload}"]), None, ["{m}.emit('k', 1)"]))
            self._register(self.mods["events"].items[-1], "events")

    # ------------------------------------------------------------ debt instances
    def new_instance(self, ptype, rel):
        rng = self.rng
        self.counter += 1
        k = str(self.counter)
        ent = rng.choice(self.ents)
        if ptype == "dependency_structure":
            return self._dependency(ent, k, rel)
        tpl = rng.choice(D.TEMPLATES[ptype])
        spec = tpl(ent, self.st, rng, k)
        return self._install(spec, ent, rel, k)

    def _install(self, spec, ent, rel, k):
        if spec.template == "private_access" and (ent.E + "Store") not in self.names:
            self.add_clean(B.a_store, ent, rel)
        mod = self.pick_mod(spec.mod_kind)
        iid = "%s-D%02d" % (self.pkg, len(self.instances) + 1)
        inst = Instance(iid, spec, ent, rel)
        for imp in spec.imports:
            self.mods[mod].add_import(imp)
        for p in spec.prelude:
            if p not in self.mods[mod].prelude:
                self.mods[mod].prelude.append(p)
        for u in spec.units:
            if isinstance(u, Fn):
                u.name = self.uname(u.name)
        self.add_items(mod, spec.units, inst, rel)
        inst.module = mod
        inst.units = [m for u in spec.units for m in (u.methods if isinstance(u, Cls) else [u])]
        self._finish(inst)
        return inst

    def _finish(self, inst):
        rp, rng = self.rp, self.rng
        lines = sum(len(u.body) + 1 for u in inst.units) or 2
        inst.rate = unit_rate(rng, lines, rp["pf_d"], rp["dmult"])
        inst.frozen = inst.rate == 0.0
        for u in inst.units:
            u.rate = inst.rate / max(1, len([x for x in inst.units if x.tune or x.tune_sig]))
        self.instances.append(inst)

    def _edge(self, a, b):
        return any(i.text in ("from . import %s" % b, "from .%s import *" % b) or i.text.startswith("from .%s import" % b) for i in self.mods[a].imports)

    def _dependency(self, ent, k, rel):
        rng = self.rng
        names = [n for n in self.mods if n != "cli"]
        layer = self.layer
        options = []
        for lo in names:
            for hi in list(self.mods):
                if layer[lo] < layer[hi] and (lo, hi) not in self.pairs_used:
                    options.append((lo, hi))
        kind = rng.choice(["cycle", "wildcard", "layer", "layer"])
        if kind in ("cycle", "wildcard") and not options:
            kind = "layer"
        iid = "%s-D%02d" % (self.pkg, len(self.instances) + 1)
        if kind == "layer":
            los = [n for n in names if layer[n] < max(layer.values())]
            lo = rng.choice(los)
            his = [n for n in self.mods if layer[n] > layer[lo]]
            hi = rng.choice(his)
            n = self.uname("notify_upstream_%s" % k)
            b, t = B.mk(["from . import %s" % hi, "limit = 5" + B.TUNE, "return str(%s.__name__)[:limit] + str(len(rec))" % hi])
            cb = B.mk(["return str(len(rec))"])
            spec = D.Spec("dependency_structure", "layer_violation", "function", "utils", [Fn(n, "rec", b, t, None, ["{m}.%s({\"a\": 1})" % n])], clean={0: cb})
            mod = lo
            inst = Instance(iid, spec, ent, rel)
            self.add_items(mod, spec.units, inst, rel)
            inst.module = mod
            inst.units = list(spec.units)
            self._finish(inst)
            return inst
        lo, hi = rng.choice(options)
        self.pairs_used.add((lo, hi))
        if kind == "cycle":
            if not self._edge(hi, lo):
                self.mods[hi].add_import("from . import %s" % lo)
            line = self.mods[lo].add_import("from . import %s" % hi, "back reference")
            spec = D.Spec("dependency_structure", "import_cycle", "module", lo, [], region="import")
            template = "import_cycle"
            host = lo
        else:
            line = self.mods[hi].add_import("from .%s import *" % lo, "noqa: F403")
            spec = D.Spec("dependency_structure", "wildcard_import", "module", hi, [], region="import")
            template = "wildcard_import"
            host = hi
        inst = Instance(iid, spec, ent, rel)
        inst.module, inst.stmt, inst.import_line = host, line.text, line
        inst.removable = [(host, line)]
        self.dirty.update([lo, hi])
        self._finish(inst)
        inst.import_rate = inst.rate
        return inst

    def repay(self, inst, rel):
        inst.repaid_rel = rel
        if inst.region_kind == "import":
            self.mods[inst.module].drop_import(inst.import_line)
            self.dirty.add(inst.module)
        elif inst.region_kind == "class":
            self.mods[inst.module].items = [it for it in self.mods[inst.module].items if it not in inst.spec.units]
            for u in inst.units:
                self.units = [x for x in self.units if x is not u]
            self.dirty.add(inst.module)
        else:
            for i, u in enumerate(inst.units):
                if i in inst.spec.clean:
                    body, tune = inst.spec.clean[i]
                    u.set_body(body, tune)
                u.inst = None
                u.rate = unit_rate(self.rng, len(u.body) + 1, self.rp["pf_c"]) if u.tune else 0.0
            self.dirty.add(inst.module)

    # ------------------------------------------------------------ editing
    def edit(self, unit, rel, kind="modify"):
        rng = self.rng
        inst = getattr(unit, "inst", None)
        if kind == "grow":
            unit.grow(rng, max(1, int(rng.lognormvariate(1.1, 1.0))))
            n = 1
        else:
            k = 1
            while rng.random() < 0.62 and k < 8:
                k += 1
            if rng.random() < 0.2:                       # occasional large rework (heavy tail of the event size)
                k = max(k, int(rng.lognormvariate(2.8, 0.7)))
            n = unit.modify(rng, k)
        if n:
            self.dirty.add(unit.mod)
            if inst is not None:
                inst.edits.append((rel, kind, n))
        return n

    def edit_import(self, inst, rel):
        inst.import_line.ver += 1
        self.dirty.add(inst.module)
        inst.edits.append((rel, "modify", 1))
        return 1

    # ------------------------------------------------------------ rendering
    def render(self, name):
        return self.mods[name].render(self.st)

    def files(self, names=None):
        out = {}
        for n in (names or self.mods):
            out["%s/%s.py" % (self.pkg, n)] = self.render(n)
        return out

    def smoke_script(self):
        lines = ["import importlib, sys, traceback", "sys.path.insert(0, '.')", "fails = []", "soft = []", "missing = []", "mods = {}", "for n in %r:" % list(self.mods),
                 "    mods[n] = importlib.import_module('%s.' + n)" % self.pkg]
        for n, m in self.mods.items():
            for it in m.items:
                samp = it.sample if hasattr(it, "sample") else []
                if isinstance(it, Cls) and samp:
                    samp = ["\n".join(samp)]
                soft = getattr(it, "was_debt", False) or (isinstance(it, Cls) and any(getattr(x, "was_debt", False) for x in it.methods))
                for s in samp:
                    stmt = s.replace("{m}", "mods[%r]" % n)
                    lines += ["try:", "    exec(compile(%r, 'smoke', 'exec'), {'mods': mods, 'm': mods[%r]})" % (stmt, n), "except Exception as exc:", "    %s.append((%r, %r, repr(exc)))" % ('soft' if soft else '(missing if ("has no attribute" in str(exc) and "module" in str(exc)) else fails)', n, stmt[:60])]
        lines += ["print('SMOKE', len(fails), 'soft', len(soft), 'missing', len(missing))", "for f in fails[:8]:", "    print(f)"]
        return "\n".join(lines)


# ====================================================================== history
CLK = dict(sigma=1.0, p=0.10, mult=15.0)
if os.environ.get("SYN_CLK"):
    CLK.update(dict(zip(("sigma", "p", "mult"), map(float, os.environ["SYN_CLK"].split(",")))))


STEP = dict(patch=(0.58, 0.3, 37), minor=(0.33, 1.8, 104), major=(0.09, 1.8, 98))      # share, activity multiplier, days between releases (real, 33 repositories)


def release_plan(rng, n, rho):
    """for every release: (step, days, activity). Activity = step multiplier x lognormal jitter (sigma 0.45), independent between releases unless rho > 0 (counter-regime)."""
    x, out = rng.gauss(0, 1), []
    for i in range(n):
        u, step = rng.random(), "patch"
        acc = 0.0
        for k, (p, _, _) in STEP.items():
            acc += p
            if u <= acc:
                step = k
                break
        x = rho * x + math.sqrt(1 - rho * rho) * rng.gauss(0, 1)
        a = STEP[step][1] * math.exp(0.45 * x - 0.45 ** 2 / 2) if rho == 0 else STEP[step][1] * math.exp(1.0 * x - 0.5)
        days = max(5, int(STEP[step][2] * math.exp(rng.gauss(0, 0.35))))
        out.append((step, days, a))
    return out


def poisson(rng, lam):
    L, k, p = math.exp(-min(lam, 30)), 0, 1.0
    while True:
        k += 1
        p *= rng.random()
        if p <= L:
            return k - 1


class Git:
    def __init__(self, path):
        self.path = path
        os.makedirs(path, exist_ok=True)
        self.run("init", "-q", "-b", "main")
        self.run("config", "gc.auto", "0")

    def run(self, *a, env=None):
        e = dict(os.environ)
        if env:
            e.update(env)
        subprocess.run(["git", "-C", self.path, *a], check=True, env=e, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def commit(self, files, msg, author, when):
        for rel, text in files.items():
            p = os.path.join(self.path, rel)
            os.makedirs(os.path.dirname(p), exist_ok=True)
            with open(p, "w") as fh:
                fh.write(text)
        self.run("add", "-A")
        iso = when.strftime("%Y-%m-%dT%H:%M:%S +0000")
        env = dict(GIT_AUTHOR_NAME=author[0], GIT_AUTHOR_EMAIL=author[1], GIT_AUTHOR_DATE=iso, GIT_COMMITTER_NAME=author[0], GIT_COMMITTER_EMAIL=author[1], GIT_COMMITTER_DATE=iso)
        self.run("commit", "-q", "-m", msg, "--allow-empty", env=env)

    def tag(self, name):
        self.run("tag", name)


def simulate(dom, seed, regime, out_repo, major=None, tier=None):
    """returns the manifest (dict). The repository is created at out_repo (bare)."""
    P = Project(dom, seed, regime, tier)
    rng, R = P.rng, P.R
    tmp = tempfile.mkdtemp(prefix="synth_")
    git = Git(tmp)
    base = datetime(2019, 1, 7, 9, 0, tzinfo=timezone.utc)
    commits, releases = [], []
    owner = {n: AUTHORS[i % len(AUTHORS)] for i, n in enumerate(sorted(P.mods))}
    plan_ = release_plan(rng, R, P.rp["rho"])
    clk = [p[2] for p in plan_]
    ctime = [base]

    def do_commit(files, msg, kind, rel, mod=None, extra=None):
        author = owner.get(mod, AUTHORS[0]) if mod else rng.choice(AUTHORS)
        ctime[0] = ctime[0] + timedelta(minutes=rng.randint(20, 400))
        git.commit(files, msg, author, ctime[0])
        rec = dict(idx=len(commits), release=rel, kind=kind, message=msg, author=author[0], date=ctime[0].isoformat(), files=sorted(files))
        if extra:
            rec.update(extra)
        commits.append(rec)
        return rec

    written = {}

    def flush():
        names = sorted(P.dirty)
        f = {k: v for k, v in P.files(names).items() if written.get(k) != v}
        written.update(f)
        P.dirty.clear()
        return f

    # ---- schedule of the debt instances
    types = ["complexity", "concurrency", "coupling_cohesion", "dependency_structure", "security"]
    major = major or rng.choice(types)
    minors = rng.sample([t for t in types if t != major], 2)
    n_major = rng.randint(*P.P["major"])
    plan = [major] * n_major + minors
    sched = []
    for pt in plan:
        legacy = rng.random() < 0.4
        rel = 1 if legacy else rng.randint(2, max(2, min(R - 2, int(0.6 * R))))
        sched.append((rel, pt))
    sched.sort()

    # ---- release 1: scaffold, then the legacy debt
    P.build_initial()
    initial = P.files()
    initial["%s/__init__.py" % P.pkg] = '"""%s: %s."""\n__version__ = "0.1"\n' % (P.pkg, dom["title"])
    initial["README.md"] = "# %s\n\nSmall demo project (%s).\n" % (dom["title"], dom["slug"])
    P.dirty.clear()
    written.update(initial)
    do_commit(initial, "Initial commit", "initial", 1)
    rel_commit = {1: []}
    intro = [s for s in sched if s[0] == 1]
    for _, pt in intro:
        inst = P.new_instance(pt, 1)
        extra_events = []
        mixed = rng.random() < 0.5
        if mixed:
            cand = [u for u in P.units if getattr(u, "inst", None) is None and u.tune and u.rate > 0]
            if cand:
                P.edit(rng.choice(cand), 1)
                inst.mixed = True
        mod = inst.module
        rec = do_commit(flush(), "add %s %s" % (inst.ent.e, rng.choice(NOUNS)), "debt_introduced", 1, mod, dict(instance=inst.id))
        inst.intro_commit = rec["idx"]
    # extra feature commits so that release 1 has more than one commit
    for _ in range(rng.randint(1, 2)):
        if P.combos_left:
            a, e = P.combos_left.pop()
            mod, items = P.add_clean(a, e, 1)
            do_commit(flush(), "add %s" % (items[0].name if hasattr(items[0], "name") else "feature"), "feature", 1, mod)
    git.tag("v0.1")
    releases.append(dict(tag="v0.1", release=1, activity=round(clk[0], 4), commit=len(commits) - 1, step="major", days=0))
    edited_prev = defaultdict(list)       # unit -> releases in which it was edited
    mod_prev = defaultdict(set)
    dmod_prev = defaultdict(set)

    # ---- releases 2..R
    rel_start = [base]
    for t in range(2, R + 1):
        a = clk[t - 1]
        rel_start[0] = rel_start[0] + timedelta(days=plan_[t - 1][1])
        ctime[0] = max(ctime[0], rel_start[0])
        events = []
        edited_now = defaultdict(list)
        # scheduled debt introductions
        for rel, pt in sched:
            if rel == t:
                events.append(("intro", pt))
        # repayments
        for inst in P.instances:
            if inst.repaid_rel is None and inst.intro_rel < t - 1:
                hot = len([e for e in inst.edits if e[0] < t])
                p = 0.045
                if rng.random() < p:
                    events.append(("repay", inst))
        for u in list(P.units):                                  # refactoring: a big clean function is split (its padding removed) with a hazard of 4.5 % per release
            if getattr(u, "inst", None) is None and getattr(u, "padn", 0) >= 12 and rng.random() < 0.045 * (1.0 if P.tier != "H" else 1.0):
                events.append(("refactor", u))
        # edits of clean functions
        def eff(rate, unit_key, mod, inst=None, created=None):
            r = rate * a
            if created is not None:                              # activity is highest right after the code appears and settles (real: odds ratio 0.93 per release of age)
                r *= 1.0 + 1.5 * math.exp(-(t - created) / 2.0)
            if P.rp["decay"]:
                recent = sum(0.5 ** (t - j) for j in edited_prev[unit_key] if j < t)
                r *= 0.15 + 5.0 * recent
            if P.rp["contagion"] and inst is not None and (dmod_prev[mod] - {unit_key}):
                r *= 8.0
            return r
        for u in list(P.units):
            if getattr(u, "inst", None) is None and u.rate > 0:
                for _ in range(min(3, poisson(rng, eff(u.rate, id(u), u.mod, None, getattr(u, "created", None))))):
                    events.append(("edit", u))
        for inst in P.instances:
            if inst.repaid_rel is not None:
                continue
            if inst.region_kind == "import":
                if inst.rate > 0:
                    for _ in range(min(3, poisson(rng, eff(inst.rate, id(inst), inst.module, inst, inst.intro_rel)))):
                        events.append(("edit_import", inst))
                continue
            if inst.rate > 0:
                for _ in range(min(3, poisson(rng, eff(inst.rate, id(inst), inst.module, inst, inst.intro_rel)))):
                    events.append(("edit_inst", inst))
        # new features
        for _ in range(poisson(rng, P.P["feat"] * min(a, 3.0))):
            events.append(("feature", None))
        rng.shuffle(events)
        i = 0
        while i < len(events):
            chunk = events[i:i + rng.randint(1, 3)]
            i += len(chunk)
            msg_parts, kinds, mod_hint, extra = [], [], None, {}
            for ev in chunk:
                kind = ev[0]
                if kind == "intro":
                    inst = P.new_instance(ev[1], t)
                    inst.intro_commit = len(commits)
                    extra["instance"] = inst.id
                    kinds.append("debt_introduced")
                    mod_hint = inst.module
                    msg_parts.append("add %s %s" % (inst.ent.e, rng.choice(NOUNS)))
                    if len(chunk) > 1:
                        inst.mixed = True
                elif kind == "repay":
                    inst = ev[1]
                    P.repay(inst, t)
                    extra["repaid"] = inst.id
                    kinds.append("debt_repaid")
                    mod_hint = inst.module
                    msg_parts.append(rng.choice(MSG_REPAY).format(f=(inst.units[0].name if inst.units else inst.module), m=inst.module))
                elif kind == "refactor":
                    u = ev[1]
                    if u not in P.units or getattr(u, "padn", 0) < 12:
                        continue
                    k_ = u.padn
                    u.body = u.body[k_:]
                    u.tune = [x - k_ for x in u.tune if x >= k_]
                    u.padn = 0
                    P.dirty.add(u.mod)
                    kinds.append("refactor")
                    mod_hint = u.mod
                    msg_parts.append(rng.choice(MSG_REPAY).format(f=u.name, m=u.mod))
                elif kind == "edit":
                    u = ev[1]
                    if u not in P.units:
                        continue
                    if P.edit(u, t, "grow" if rng.random() < 0.15 else "modify"):
                        edited_now[id(u)].append(t)
                        mod_prev_add = u.mod
                        kinds.append("edit")
                        mod_hint = u.mod
                        msg_parts.append(rng.choice(MSG_MOD).format(m=u.mod, f=u.name, e=P.ents[0].e))
                elif kind == "edit_inst":
                    inst = ev[1]
                    if inst.repaid_rel is not None:
                        continue
                    cand = [u for u in inst.units if u.tune or u.tune_sig]
                    if cand:
                        u = rng.choice(cand)
                        if P.edit(u, t, "grow" if rng.random() < 0.2 else "modify"):
                            edited_now[id(inst)].append(t)
                            kinds.append("edit_debt")
                            mod_hint = inst.module
                            msg_parts.append(rng.choice(MSG_MOD).format(m=inst.module, f=u.name, e=inst.ent.e))
                elif kind == "edit_import":
                    inst = ev[1]
                    if inst.repaid_rel is not None:
                        continue
                    P.edit_import(inst, t)
                    edited_now[id(inst)].append(t)
                    kinds.append("edit_debt")
                    mod_hint = inst.module
                    msg_parts.append("update imports in %s" % inst.module)
                elif kind == "feature":
                    if P.combos_left:
                        ar, e = P.combos_left.pop()
                    else:
                        ar, e = rng.choice([x for x in B.ARCHETYPES if x is not B.a_store]), rng.choice(P.ents)
                    mod, items = P.add_clean(ar, e, t)
                    mod_hint = mod
                    kinds.append("feature")
                    msg_parts.append("add %s" % getattr(items[0], "name", "feature"))
            files = flush()
            if not files:
                continue
            rec = do_commit(files, "; ".join(msg_parts)[:100], "+".join(sorted(set(kinds))) or "misc", t, mod_hint, extra)
            if "instance" in extra:
                for inst in P.instances:
                    if inst.id == extra["instance"]:
                        inst.intro_commit = rec["idx"]
            if "repaid" in extra:
                for inst in P.instances:
                    if inst.id == extra["repaid"]:
                        inst.repay_commit = rec["idx"]
        for k_, v in edited_now.items():
            edited_prev[k_] += v
        mod_prev = defaultdict(set)
        dmod_prev = defaultdict(set)
        for inst in P.instances:
            if id(inst) in edited_now:
                dmod_prev[inst.module].add(id(inst))
        if not any(c["release"] == t for c in commits):
            do_commit({"README.md": "# %s\n\nSmall demo project (%s). Release %d.\n" % (dom["title"], dom["slug"], t)}, "docs: update readme", "docs", t)
        git.tag("v0.%d" % t)
        releases.append(dict(tag="v0.%d" % t, release=t, activity=round(a, 4), commit=len(commits) - 1, step=plan_[t - 1][0], days=plan_[t - 1][1]))

    # ---- hashes
    hashes = subprocess.run(["git", "-C", tmp, "rev-list", "--reverse", "HEAD"], capture_output=True, text=True).stdout.split()
    assert len(hashes) == len(commits), (len(hashes), len(commits))
    for c, h in zip(commits, hashes):
        c["hash"] = h
    smoke = P.smoke_script()
    if os.path.exists(out_repo):
        shutil.rmtree(out_repo)
    subprocess.run(["git", "clone", "-q", "--bare", tmp, out_repo], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if not os.environ.get("SYN_NOGC"):
        subprocess.run(["git", "-C", out_repo, "gc", "-q", "--prune=now"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    shutil.rmtree(tmp)
    ins = []
    for inst in P.instances:
        ins.append(dict(
            id=inst.id, ptype=inst.ptype, template=inst.template, granularity=inst.granularity, region_kind=inst.region_kind, module=inst.module,
            file="%s/%s.py" % (P.pkg, inst.module), entity=inst.ent.E,
            quals=[u.name for u in inst.spec.units] if inst.region_kind != "import" else [], stmt=inst.stmt,
            intro_release=inst.intro_rel, intro_commit=inst.intro_commit, intro_hash=commits[inst.intro_commit]["hash"] if inst.intro_commit is not None else None,
            parent_hash=commits[inst.intro_commit - 1]["hash"] if inst.intro_commit else None, mixed=inst.mixed,
            repaid_release=inst.repaid_rel, repay_commit=getattr(inst, "repay_commit", None),
            latent_rate=round(inst.rate, 5), frozen=inst.frozen, sim_edits=inst.edits))
    final_files = {n: m.render(P.st).count("\n") for n, m in P.mods.items()}
    return dict(
        id=P.pkg, title=dom["title"], domain=dom["slug"], source=dom["src"], tier=P.tier, seed=seed, regime=regime, releases=R,
        style=dict(docstrings=P.st.doc, record_var=P.st.rv, verbs=P.st.verbs), major_type=major, minor_types=minors, n_major=n_major,
        modules=list(P.mods), layer=P.layer, loc_by_module=final_files, loc=sum(final_files.values()),
        regime_params={k: v for k, v in P.rp.items()}, activity=[round(x, 4) for x in clk], release_table=releases, commits=commits, instances=ins, smoke=smoke)
