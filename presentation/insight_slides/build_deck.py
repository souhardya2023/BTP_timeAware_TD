"""Adds the results (precise) and real-project insight slides to the final deck.
Input  ../TD-presentation.pptx (slides 1-14, 20-21 are kept; the old result slides 15-18 and the limits slide 19 are replaced)
Output ../TD-presentation-insights.pptx
Style: Arial, one text colour, body 10.5 pt, key line 12 pt bold, slide title 24 pt bold; plots from make_figs.py; one plain table per slide at most."""
import copy, io, os
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.oxml.ns import qn
from lxml import etree

HERE = os.path.dirname(os.path.abspath(__file__)); FIG = os.path.join(HERE, "figs")
INK = RGBColor(0x11, 0x11, 0x11); FONT = "Arial"; BODY, KEY, TITLE = 10.5, 12, 24

prs = Presentation(os.path.join(HERE, "..", "TD-presentation.pptx"))
blank = [l for l in prs.slide_layouts if l.name == "BLANK"][0]
logo = None
for sh in prs.slides[14].shapes:
    if sh.shape_type == 13 and sh.left > 8000000:
        logo = sh.image.blob


def run(p, text, size, bold=False):
    r = p.add_run(); r.text = text; f = r.font; f.name = FONT; f.size = Pt(size); f.bold = bold; f.color.rgb = INK
    return r


def textbox(s, x, y, w, h, items):
    """items: list of (text, key) -> bullets; key lines are 16 pt bold, the others 14 pt"""
    tb = s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h)); tf = tb.text_frame; tf.word_wrap = True
    for i, (t, key) in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        pPr = p._p.get_or_add_pPr(); pPr.set("marL", "228600"); pPr.set("indent", "-228600")
        bu = etree.SubElement(pPr, qn("a:buChar")); bu.set("char", "•")
        p.space_after = Pt(7)
        run(p, t, KEY if key else BODY, key)
    return tb


def new_slide(title, notes=""):
    s = prs.slides.add_slide(blank)
    tb = s.shapes.add_textbox(Emu(365760), Emu(137160), Emu(7863480), Emu(500000)); tf = tb.text_frame; tf.word_wrap = True
    run(tf.paragraphs[0], title, TITLE, True)
    s.shapes.add_picture(io.BytesIO(logo), Emu(8339400), Emu(109800), Emu(456840), Emu(511560))
    nb = s.shapes.add_textbox(Emu(8412480), Emu(4846320), Emu(365400), Emu(200880)); nb.name = "slide_no"; run(nb.text_frame.paragraphs[0], "0", 9)
    if notes: s.notes_slide.notes_text_frame.text = notes
    return s


SCEN = os.path.join(HERE, "..", "..", "scenario_analysis", "figures")


def pic(s, name, x, y, w):
    return s.shapes.add_picture(os.path.join(SCEN if name.startswith("s") and name[1].isdigit() else FIG, name), Inches(x), Inches(y), width=Inches(w))


def table(s, x, y, w, rows, colw, rowh=0.3):
    gs = s.shapes.add_table(len(rows), len(rows[0]), Inches(x), Inches(y), Inches(w), Inches(rowh * len(rows)))
    tbl = gs.table
    tbl._tbl.tblPr.find(qn("a:tableStyleId")).text = "{5940675A-B579-460E-94D1-54222C63F5DA}"   # no style, plain grid
    tbl.first_row = False; tbl.horz_banding = False
    for j, cw in enumerate(colw): tbl.columns[j].width = Inches(cw)
    for i, r in enumerate(rows):
        tbl.rows[i].height = Inches(rowh)
        for j, v in enumerate(r):
            c = tbl.cell(i, j); c.fill.background(); c.margin_top = c.margin_bottom = Inches(0.03); c.vertical_anchor = MSO_ANCHOR.MIDDLE
            p = c.text_frame.paragraphs[0]; p.alignment = PP_ALIGN.LEFT if j == 0 else PP_ALIGN.CENTER
            run(p, str(v), BODY, i == 0)
    return gs


new = []
# ---- Result 1
s = new_slide("Result 1: debt type, with and without fix time",
              "Level 1. 61 pairs, 10 best features plus random forest, delta layout. Fix time helps a lot inside known projects (0.79 to 0.92 stratified, 0.84 to 0.94 over 20 random splits). On a project the model has not seen the accuracy is 0.43 to 0.51, close to the majority class 0.43. So the type is learnable inside known projects, not yet across projects.")
pic(s, "r1_type_accuracy.png", 0.35, 1.0, 5.6)
textbox(s, 6.2, 1.1, 3.5, 3.6, [("Fix time lifts accuracy from 0.79 to 0.92 on stratified folds", True),
                                 ("20 random splits: 0.84 to 0.94", False),
                                 ("New projects: 0.43 to 0.51, close to the majority class 0.43", True),
                                 ("Type is learnable inside known projects, not yet across projects", False)]); new.append(s)
# ---- Result 2
s = new_slide("Result 2: ranking by predicted interest",
              "Level 2. Rank the instances of one release by predicted interest and check how much of the next release's interest sits in the top k percent. Leave-one-repository-out, 123 repo-release groups. Persistence, the interest an instance already paid, is as good as the two-part model.")
pic(s, "r2_capture_9repos.png", 0.35, 1.0, 5.3)
textbox(s, 5.9, 1.0, 3.8, 1.9, [("9 repositories: top 20% by persistence captures 39% of next-release interest; random gets 20%", True),
                                 ("The two-part model gets 38%: no gain over persistence", False)])
table(s, 5.9, 3.0, 3.7, [["Top 20%", "Capture", "Lift"], ["Random", "20%", "1.0"], ["Persistence", "38.8%", "1.9"], ["Two-part model", "38.5%", "1.9"]], [1.7, 1.1, 0.9], 0.34)
new.append(s)
# ---- Result 3
s = new_slide("Result 3: 33 repositories, size and history",
              "Same ranking task on all 33 repositories, leave-one-repository-out, 427 groups. Size alone is worse than persistence by 5.4 points. A logistic model on size and history is 2.3 points above persistence at 20 percent (interval minus 0.1 to 4.6) and 3.0 at 30 percent (0.8 to 5.2). The effect is real but small. AUC measures where interest occurs: 0.62, 0.75, 0.79.")
pic(s, "r3_capture_33repos.png", 0.35, 1.0, 5.3)
textbox(s, 5.9, 1.0, 3.8, 1.9, [("Size + history captures 41.5% in the top 20%; persistence 39.8%", True),
                                 ("Gain over persistence: +2.3 points at 20%, +3.0 at 30%", False)])
table(s, 5.9, 3.0, 3.7, [["Rule", "AUC"], ["Size only", "0.62"], ["Persistence", "0.75"], ["Size + history", "0.79"]], [2.3, 1.4], 0.34)
new.append(s)
# ---- data
s = new_slide("Real projects: 33 repositories",
              "To learn how debt behaves in real code the same pipeline was run on 33 open-source repositories: the 9 of the earlier study and 24 new ones. Last 20 release tags per repository. Debt instance is a function with a structural smell. Interest is the changed lines inside a persisting debt function, converted to person-months with COCOMO II.")
table(s, 0.4, 1.1, 4.7, [["Item", "Count"], ["Repositories", "33 (16 Python, 17 C/C++)"], ["Releases per repository", "last 20"], ["Debt instances", "11,503"], ["Instance-releases", "148,524"],
                         ["Interest events", "27,583"], ["Interest", "449 person-months"], ["Commits analysed", "20,988"]], [2.2, 2.5], 0.38)
textbox(s, 5.5, 1.1, 4.2, 3.6, [("Debt: Long Method, Complex Method or Many Parameters, same detector everywhere", False),
                                 ("Interest: changed lines inside a persisting debt function, in person-months (COCOMO II)", False),
                                 ("Three insights follow, one plot each", True)]); new.append(s)
# ---- insights
s = new_slide("Insight 1: interest is concentrated and repeats",
              "Left: instances sorted by interest; the top 10 percent hold 80 percent of all interest and the top 20 percent hold 91 percent. Right: the share of instances that pay in the next release by the number of earlier events: 8, 18, 34, 30, 43 percent. With size and repository controlled, an event in the previous release pair has odds ratio 4.6 (2.5 to 8.5) in the C/C++ repositories but only 1.4 (0.9 to 2.2) in the Python ones. About a third of the debt never pays in 10 or more releases.")
pic(s, "i1_concentration_memory.png", 0.7, 0.85, 8.3)
textbox(s, 0.5, 3.95, 9.0, 1.5, [("10% of the debt instances hold 80% of all interest", True),
                                  ("An instance that paid before pays again: 8% with no past event, 43% with five or more; size-adjusted odds ratio 4.6 in C/C++, only 1.4 in Python", False),
                                  ("Repay the few hot instances; history finds them", False)]); new.append(s)
s = new_slide("Insight 2: debt is not avoided",
              "The earlier claim that developers avoid debt came from dividing by all changed lines, which include new code, deleted code and declarations. Restricted to functions present in both releases the ratio is 1.11. At equal size and repository a debt function is edited with odds ratio 1.07 (0.92 to 1.25) relative to a clean one. Interest lines grow almost linearly with size (exponent 0.93). So size is exposure, and size plus history is the baseline.")
pic(s, "i2_not_avoided.png", 0.7, 0.85, 8.3)
textbox(s, 0.5, 3.95, 9.0, 1.5, [("The earlier 'debt is avoided' (0.33) was an artefact of counting new and deleted code", True),
                                  ("At equal size a debt function is edited as often as a clean one (odds ratio 1.07)", False),
                                  ("Bigger functions are edited more; size and history together beat persistence by 2 to 3 points", False)]); new.append(s)
s = new_slide("Insight 3: the release type is the clock",
              "615 release pairs. Share of instances paying interest: patch 9 percent, minor 28 percent, major 31 percent. 58 percent of the release pairs are patch releases. Release type plus days since the previous tag explains R squared 0.27 of the within-repository release interest and is known in advance. Commits (0.54) and changed lines (0.70) explain more but are known only after the release.")
pic(s, "i3_release_clock.png", 0.7, 0.85, 8.3)
textbox(s, 0.5, 3.95, 9.0, 1.5, [("Patch releases are quiet: 9% of instances pay, against 28% (minor) and 31% (major)", True),
                                  ("The release type and the days since the last tag are known in advance: R² 0.27", False),
                                  ("Commits and changed lines explain more (0.54, 0.70) but are known only afterwards", False)]); new.append(s)
# ---- scenarios
s = new_slide("Scenarios: which patterns repeat?",
              "A scenario is a pattern: a group of debt instances, functions or commits defined by a condition. For each one the size-adjusted rate ratio is measured separately in the 16 Python and 17 C/C++ repositories, with a bootstrap interval over repositories. Circles are Python, squares are C/C++. REPEATS: both intervals exclude 1 in the same direction and at least 65 percent of repositories agree. LANGUAGE-SPECIFIC: only one language, or opposite. NOISE: no effect in either. 17 of the 23 scenarios tested are shown.")
pic(s, "s1_forest.png", 0.25, 0.8, 6.3)
textbox(s, 6.6, 0.85, 3.2, 4.2, [("What is a scenario?", True),
                                  ("A pattern: a group of functions, debt instances or commits picked by a condition, for example 'a function in the top third by size'.", False),
                                  ("How to read the plot", True),
                                  ("Dot = rate ratio: how many times more often the group has the event than the rest of the same repository at the same size. 1 = no effect.", False),
                                  ("Line = 95% interval over repositories.", False),
                                  ("Verdicts", True),
                                  ("Repeats: both languages clear of 1, same direction, 65% of repositories agree.", False),
                                  ("Language-specific: clear in one language only.", False),
                                  ("Noise: interval includes 1 in both.", False),
                                  ("17 of 23 scenarios are shown.", False)]); new.append(s)
import json
N4 = json.load(open(os.path.join(HERE, "..", "..", "scenario_analysis", "results", "s4_numbers.json")))


def fmt(p): return "n/a" if not p else f"{p['rr']:.2f} ({p['lo']:.2f} to {p['hi']:.2f})"


def scenario_slide(key, title, lead, bullets, notes):
    n = N4[key]; s = new_slide(title, notes)
    pic(s, f"s4_{key}.png", 0.3, 0.95, 4.9)
    textbox(s, 5.35, 0.85, 4.4, 3.0, [(lead.format(a=n["above1"], r=n["repos"]), True)] + [(b, False) for b in bullets])
    table(s, 5.35, 3.95, 4.0, [["Source", "Rate ratio (95% interval)"], ["Python", fmt(n["python"])], ["C/C++", fmt(n["c"])], ["Benchmark", fmt(n["synthetic"])]], [1.2, 2.8], 0.3)
    textbox(s, 0.35, 4.55, 4.8, 0.7, [("Each dot is one repository; right of the dashed line = the scenario raises the event rate.", False)])
    new.append(s)


scenario_slide("size", "Scenario 1 (repeats): size",
               "Larger functions are edited more: rate ratio above 1 in {a} of {r} repositories",
               ["Scenario: a function in the top third of its repository by size, compared with the rest of that repository.",
                "Event: the function has changed lines in a release pair.",
                "Meaning: big functions are touched more often, so they collect more interest. Size works as exposure.",
                "Why it repeats: same direction in Python, C/C++ and the benchmark, with both language intervals above 1."],
               "Repeating pattern 1. Functions in the top third of their repository by size are edited more in the same release pair than the rest: rate ratio above 1 in 29 of 32 repositories, intervals clear of 1 in both languages, and the synthetic benchmark has the same direction. Each dot is one repository.")
scenario_slide("release", "Scenario 2 (repeats): busy releases",
               "Releases with many commits make debt pay: rate ratio above 1 in {a} of {r} repositories",
               ["Scenario: a release with more commits than the median release of its repository.",
                "Event: a debt instance has changed lines in that release, so it pays interest.",
                "Meaning: when a release is busy, debt is touched more. The timing of interest follows the release, not the debt itself.",
                "Why it repeats: 27 of 28 repositories above 1, both language intervals above 1, and the benchmark (2.50) agrees."],
               "Repeating pattern 2. In releases with more commits than the repository median, many more debt instances pay interest: rate ratio above 1 in 27 of 28 repositories, intervals clear of 1 in both languages, and the benchmark has the same direction.")
scenario_slide("avoid", "Scenario 3 (noise): debt avoidance",
               "A debt function is not edited more or less than a clean one: rate ratio above 1 in only {a} of {r} repositories",
               ["Scenario: a debt function (Long Method, Complex Method or Many Parameters) compared with clean functions of the same size.",
                "If developers avoided debt the dots would sit left of 1; if debt attracted work, right of 1. They fall on both sides.",
                "Meaning: this is the old 'debt is avoided' claim; after matching on size nothing is left.",
                "Why it is noise: both intervals include 1, there is no stable direction, and the benchmark shows 0.54, so it disagrees too."],
               "Noise pattern. At the same size a debt function is edited about as often as a clean function (1.06 and 1.08, intervals include 1). Repositories fall on both sides of 1 like a coin flip. The effect is present in single repositories but does not repeat, and the benchmark shows 0.54, a different direction. This is the earlier 'debt is avoided' idea after correction.")
s = new_slide("Repeating, language-specific and noise",
              "23 scenarios: 7 repeat in both languages (6 strong, 1 weak), 9 are language-specific, 7 are noise. Memory is the example of a language-specific pattern: rate ratio 2.5 in C/C++ and 1.15 in Python (interval 0.8 to 1.6). In the synthetic benchmark the direction matches the real data in 11 of the 15 scenarios it can express, and in all 4 that repeat. There is no GPT-written code in the project yet, so the model axis is not tested.")
table(s, 0.4, 1.0, 5.0, [["Verdict", "Count", "Examples"], ["Repeats", "7", "size, release size, big commits"], ["Language-specific", "9", "memory, Many Parameters"], ["Noise", "7", "debt avoidance, bug-fix commits"]], [1.6, 1.0, 2.4], 0.4)
textbox(s, 0.4, 2.8, 5.0, 2.4, [("How a verdict is decided", True),
                                 ("Every scenario is measured at equal size, in each repository, then pooled per language.", False),
                                 ("Repeats: the 95% interval excludes 1 in the same direction in Python and in C/C++, and at least 65% of repositories agree.", False),
                                 ("Language-specific: the interval excludes 1 in one language only, or the two point opposite ways.", False),
                                 ("Noise: the interval includes 1 in both languages; the effect shows in single repositories but does not repeat.", False)])
textbox(s, 5.7, 1.0, 4.0, 4.2, [("Repeats in Python and C/C++: size, release activity, big commits create debt", True),
                                 ("Memory is language-specific: rate ratio 2.5 in C/C++, 1.15 in Python", True),
                                 ("Memory: an instance that paid in the last release pays again. Strong in C/C++, not clear in Python.", False),
                                 ("Noise: debt avoided, sibling contagion in a file, bug-fix commits creating debt", False),
                                 ("Benchmark (synthetic): same direction as real in 11 of 15 scenarios, and in all 4 that repeat", False),
                                 ("Use: build and judge a dataset on the repeating patterns; do not read the noise ones as findings", False)]); new.append(s)
# ---- code insights (what is in the code text)
CI = os.path.join(HERE, "..", "..", "code_insights"); C2 = {r.trait: r for r in __import__("pandas").read_csv(os.path.join(CI, "results", "c2_traits.csv")).itertuples()}
C4 = json.load(open(os.path.join(CI, "results", "c4_rates.json")))
K2 = __import__("pandas").read_csv(os.path.join(CI, "results", "k2_tests.csv"))


def k2(test, lang):
    r = K2[(K2.test.str.startswith(test)) & (K2.lang == lang)].iloc[0]; return r


def k2s(test, lang):
    r = k2(test, lang); return f"{r.rr:.2f} ({r.lo:.2f} to {r.hi:.2f})"
MONO = "Courier New"


def rr(t, lang):
    r = C2[t]; v = getattr(r, f"{lang}_rr")
    return "n/a" if v != v else f"{v:.2f} ({getattr(r, lang + '_lo'):.2f} to {getattr(r, lang + '_hi'):.2f})"


s = new_slide("Code traits: what is behind the debt label?",
              "The debt label only says a function is long, branchy or has many parameters. This slide reads the code text of those flagged functions and asks which visible traits go with more interest at the same size. Each row is a rate ratio (1 = no effect) with a 95 percent interval over repositories, size matched. Only the C/C++ effects are clear. Python has about 5,400 rows and no trait is clear. The calls and pointer-field traits raise interest; repeated lines lower it; the classic ugly habits show no effect.")
table(s, 0.35, 0.95, 6.0, [["Trait in the code", "C/C++", "Python"],
                           ["calls many different functions", rr("n_distinct_calls", "c"), rr("n_distinct_calls", "python")],
                           ["many pointer field accesses (->)", rr("n_arrow", "c"), "n/a"],
                           ["many NULL checks", rr("n_null_check", "c"), "n/a"],
                           ["the same line repeated", rr("dup_line_ratio", "c"), rr("dup_line_ratio", "python")],
                           ["goto", rr("n_goto", "c"), "n/a"],
                           ["unsafe string / memory calls", rr("n_unsafe", "c"), "n/a"],
                           ["malloc / free", rr("n_alloc", "c"), "n/a"],
                           ["deep nesting", rr("max_nest", "c"), rr("max_nest", "python")],
                           ["has a near-clone partner (whole repository)", k2s("A1", "c"), k2s("A1", "python")],
                           ["clone partner edited in the same release", k2s("B1", "c"), k2s("B1", "python")]], [2.6, 1.7, 1.7], 0.28)
textbox(s, 6.55, 0.85, 3.2, 4.5, [("What the label captures", True),
                                  ("Size, branches and parameter count. It does not say whether the code is copied, tangled or unsafe.", False),
                                  ("What the code text adds", True),
                                  ("Copied code is edited twice: when one copy changes, its partner usually changes in the same release (both languages).", False),
                                  ("In C/C++, interest also follows how many different things a function touches, not how ugly it looks.", False),
                                  ("Read the table as rate ratios at the same size; 1 = no effect.", False),
                                  ("Other traits: Python shows nothing clear (about 5,400 functions).", False)]); new.append(s)


def codebox(s, x, y, w, h, lines, changed):
    box = s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h)); box.line.color.rgb = INK; box.line.width = Pt(0.75)
    tf = box.text_frame; tf.word_wrap = False; tf.margin_left = tf.margin_right = Inches(0.05); tf.margin_top = tf.margin_bottom = Inches(0.03)
    for i, ln in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph(); p.space_after = Pt(0); p.space_before = Pt(0)
        txt = ln.expandtabs(4).rstrip(); txt = txt if len(txt) <= 72 else txt[:71] + "~"
        r = p.add_run(); r.text = (">" if i in changed else " ") + txt; f = r.font; f.name = MONO; f.size = Pt(7.5); f.bold = i in changed; f.color.rgb = INK


def code_slide(title, exfile, hot_cap, cold_cap, bullets, notes, tags=("hot", "cold"), by=4.5):
    ex = json.load(open(os.path.join(CI, "examples", exfile + ".json"))); s = new_slide(title, notes)
    for k, (tag, x, cap) in enumerate(((tags[0], 0.3, hot_cap), (tags[1], 5.05, cold_cap))):
        e = ex[tag]
        tb = s.shapes.add_textbox(Inches(x), Inches(0.82), Inches(4.7), Inches(0.35)); tf = tb.text_frame; tf.word_wrap = True
        run(tf.paragraphs[0], cap.format(f=e["func"], repo=e["repo"], a=e["tag"], b=e["next"], n=e.get("interest_lines", 0)), BODY + 1.5, True)
        codebox(s, x, 1.22, 4.7, 0.12 * min(len(e["text"]), 26) + 0.14, e["text"][:26], set(e["changed"]))
    textbox(s, 0.3, by, 9.4, 0.9, bullets); new.append(s)


code_slide("Code insight 1: copied code is edited twice", "ex4_clone_cochange",
           "Edited: {f} ({repo}, {a} to {b})", "Its near-copy {f}, edited too",
           [("When one copy is edited, its clone is edited in the same release: %.0f%% of the time in C/C++ and %.0f%% in Python, against %.0f%% and %.0f%% for a same-size function that is not a clone." % (100 * k2("B1", "c").p_partner, 100 * k2("B1", "python").p_partner, 100 * k2("B1", "c").p_control, 100 * k2("B1", "python").p_control), True),
            ("Co-change rate ratio %s in C/C++ and %s in Python; every repository agrees. Left and right are near-copies (similarity 0.81) and both signatures changed in 3.0.0. A copy alone is not edited more (C/C++ %s), so the cost is hidden: each change is repeated." % (k2s("B1", "c"), k2s("B1", "python"), k2s("A1", "c")), False)],
           "Code insight 1. A whole-repository near-clone detector (renamed identifiers, numbers and strings are normalised, generic boilerplate shingles are dropped; similarity 0.6 or more) finds clone pairs. When one function of a pair is edited in a release pair, its partner is edited in the same release pair in 81 percent of cases in C/C++ and 96 percent in Python, against 47 and 49 percent for a non-clone function of similar size in the same file, directory or repository. Rate ratio 1.74 (1.54 to 2.11) in C/C++ and 1.98 (1.49 to 5.09) in Python, every repository above 1. The result holds without test and vendor paths, with close clones only, with one random partner per function (1.64 and 2.03) and with the partner in another file. At function level a clone is not edited more often: C/C++ 0.82 (0.62 to 0.96), Python 1.17 (0.91 to 1.66, unclear). An earlier cruder measure, which looked only at functions in the same files, showed no effect at all; the proper detector changes the answer.",
           tags=("a", "b"), by=3.1)
code_slide("Code insight 2: touches many things", "ex1_many_callees",
           "Paid interest: {f} ({repo}), {n} line (>)", "No interest: {f}, same size",
           [("At the same size, C/C++ functions that call many different functions pay interest more often: %.0f%% against %.0f%% expected, in 15 of 17 repositories." % (100 * C4["many_callees|c"]["with_trait"], 100 * C4["many_callees|c"]["expected"]), True),
            ("Left: ten different setters in a row, so any new field means an edit here. Right: same length, only two different calls. Python: not confirmed (1.04).", False)],
           "Insight 1 from reading the code text. Distinct callees is the number of different functions a function calls. At the same size and in the same repository, C/C++ functions in the top quarter on this trait had interest in 27 percent of release pairs against 18 percent expected, rate ratio 1.47 (1.31 to 1.61), above 1 in 15 of 17 repositories. Pointer field accesses show the same kind of effect (1.34). In Python the trait is not clear (1.04). The pair is chosen by a fixed rule: same repository and release, same size, one that paid interest and one that did not.")
code_slide("Code insight 3: repeated lines stay quiet", "ex2_repeated_lines",
           "Paid interest: {f} ({repo}), {n} line (>)", "No interest: {f}, repeated pairs",
           [("Functions that repeat the same lines are touched less: %.0f%% with interest against %.0f%% expected, and 12 of 17 repositories are below expected." % (100 * C4["repeated_lines|c"]["with_trait"], 100 * C4["repeated_lines|c"]["expected"]), True),
            ("Right: mirrored checks, the same pattern again and again, complexity 12. It looks like the worst debt, yet it was not touched. Likely reason: a fixed list of cases rarely changes. Python: no clear effect (1.09).", False)],
           "Insight 2. Duplicate line ratio is the share of meaningful lines that appear at least twice inside the function. In C/C++ the top quarter of this trait at equal size had interest in 17 percent of pairs against 23 percent expected, rate ratio 0.74 (0.68 to 0.82). The reason given on the slide is a likely explanation, not tested. In Python the effect is not clear.")
code_slide("Code insight 4 (noise): ugly C habits", "ex3_ugly_habits_c",
           "Paid interest: {f} ({repo}), {n} line (>)", "No interest: {f}, same habit",
           [("goto, unsafe string and memory calls, malloc / free and deep nesting all show rate ratios between 0.96 and 1.04, and every interval includes 1.", True),
            ("Both functions use goto cleanup in the same style; the habit does not tell which one will be edited. These habits matter for bugs and safety, not for how often code is edited. This work measured interest, not bugs.", False)],
           "Insight 3 is the noise case at code level. Counts of goto, unsafe calls, allocation calls and deep nesting were each tested at equal size in the C/C++ repositories: rate ratios 0.96 to 1.04 with intervals that include 1. They look like debt to a reader but do not predict interest. This work did not measure bugs or security, so it says nothing about their importance there.")
s = new_slide("Reverse engineering the scenarios",
              "A decision tree on instance features (size, complexity, type, age, history, file) is fitted on some repositories; each leaf with a high or low event rate relative to its own release is a rule. Each rule is then checked on repositories it never saw. Rules from Python hold in C/C++ (5 of 5); rules from C/C++ mostly fail in Python (1 of 5) because the C/C++ history effect is stronger. Random halves: 143 of 161 rules repeat. Control: with event labels shuffled inside each release and size bin, 80 percent of rules still repeat, because size and history features carry structure; so replication alone does not prove a signal.")
pic(s, "s2_rules_replication.png", 0.3, 1.0, 5.2)
textbox(s, 5.7, 0.9, 4.1, 4.3, [("Idea: let the data propose the scenarios instead of choosing them", True),
                                 ("A decision tree is fitted on some repositories using size, complexity, type, age, history and file features. Each leaf with a high or low event rate is a rule.", False),
                                 ("The rule is then measured on repositories the tree never saw. It repeats if it keeps its direction there.", False),
                                 ("Rules found in Python hold in C/C++ (5 of 5); the other way only 1 of 5, because the history effect is stronger in C/C++", True),
                                 ("Random repository halves: 89% of 161 rules repeat", False),
                                 ("Control: with shuffled labels 80% still repeat, so this test alone does not separate signal from noise", False)]); new.append(s)
s = new_slide("Next: repeat across GPT models?",
              "Same method with the model in place of the language: generate code for the same tasks with several GPT models, detect debt, and test the scenarios that repeated here (size, type, complexity, edits after generation). A scenario that keeps its direction in every model repeats; one that does not is noise. This needs code from the models; none is in the project yet.")
textbox(s, 0.5, 1.0, 9.0, 3.9, [("Not done yet: the project has no GPT-written code", True),
                                 ("Plan: same tasks to several GPT models; same debt detector; same scenario test", False),
                                 ("Model takes the place of language: a scenario repeats if its direction holds in every model", False),
                                 ("Scenarios that flip between models are noise", False),
                                 ("Release history does not exist for generated code, so size, type and complexity scenarios come first", False)]); new.append(s)
# ---- limits
s = new_slide("Limits, and what comes next",
              "What I would not claim. The type classifier does not transfer to new projects. The synthetic benchmark reproduces real histories (AUC 0.62, 0.73, 0.79 against 0.62, 0.75, 0.79 real), but a classifier trained on its pairs scores 0.15 on the 61 real pairs, below the majority class 0.43, because the debt change is still too visible. Next: more natural pairs, smaller debt changes in the synthetic pairs, and tests on AI-written changes.")
textbox(s, 0.5, 1.0, 4.4, 3.8, [("Limits:", True), ("61 pairs; 60 injected, 1 natural", False), ("Type model: 0.51 on new projects, majority 0.43", False),
                                 ("Smells are a proxy for debt; interest is implied effort, not measured time", False), ("Size + history beats persistence by only 2 to 3 points; memory is strong in C/C++, weak in Python", False), ("GPT-model generalisation not tested: no GPT code yet", False),
                                 ("Synthetic benchmark matches real histories but a model trained on it fails on the real pairs (0.15)", False)])
textbox(s, 5.2, 1.0, 4.4, 3.8, [("Next:", True), ("More natural pairs, checked by hand", False), ("Smaller debt changes in the synthetic pairs", False), ("Rank by size + history, release type as the clock", False),
                                 ("Test on AI-written changes", False)]); new.append(s)

# ---- reorder: keep 1-14, then new, then old 20-21 ; drop old 15-19
ids = prs.slides._sldIdLst; old = list(ids)
n_old = 21; keep_front = old[:14]; drop = old[14:19]; keep_back = old[19:n_old]; added = old[n_old:]
for e in drop:
    prs.part.drop_rel(e.get(qn("r:id"))); ids.remove(e)
for e in added: ids.remove(e)
for e in added: ids.insert(14 + added.index(e), e)
for k, sl in enumerate(prs.slides, 1):
    for sh in sl.shapes:
        if sh.has_text_frame and sh.left == 8412480 and sh.top == 4846320 or sh.name == "slide_no":
            r = sh.text_frame.paragraphs[0].runs
            if r: r[0].text = str(k); r[0].font.color.rgb = INK
out = os.path.join(HERE, "..", "TD-presentation-insights.pptx"); prs.save(out); print("saved", out, len(prs.slides), "slides")
