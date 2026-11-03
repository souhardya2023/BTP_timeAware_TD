// Deck: white background, black titles, amber callouts (style of the example slides).
const pptxgen = require("pptxgenjs");
const fs = require("fs");
const P = require("./data/prio.json");
const CV = require("./data/curve.json");
const NOTES = require("./notes.js");

const INK = "111111", GREY = "666666", AMB = "1F3A5F", ORG = "1F3A5F", BLUE = "2F5F98", GRN = "2E7D4F", RED = "B23A2E", LINE = "CCCCCC";
const F = "Arial";
const pres = new pptxgen();
pres.layout = "LAYOUT_16x9";
pres.title = "Technical debt prioritisation and its evaluation";
pres.author = "Souhardya Dandapat";

const notes = [];
let n = 0, ni = 0;
function slide(title, caption, spoken) {
  const s = pres.addSlide(); n++; ni++;
  s.background = { color: "FFFFFF" };
  s.addImage({ path: "kgp_logo.png", x: 9.12, y: 0.12, w: 0.5, h: 0.56 });
  s.addText(title, { x: 0.4, y: 0.15, w: 8.6, h: 0.5, fontFace: F, fontSize: 24, bold: true, color: INK, margin: 0, valign: "middle", isTextBox: true });
  if (caption) s.addText(caption, { x: 0.4, y: 0.68, w: 9.2, h: 0.25, fontFace: F, fontSize: 11, color: GREY, margin: 0, isTextBox: true });
  s.addText(String(n), { x: 9.2, y: 5.3, w: 0.4, h: 0.22, fontFace: F, fontSize: 9, color: GREY, align: "right", margin: 0, isTextBox: true });
  const sp = NOTES[ni - 1]; if (sp) { s.addNotes(sp); notes.push([n, title, sp]); }
  return s;
}
const T = (s, text, o) => s.addText(text, Object.assign({ fontFace: F, fontSize: 11, color: INK, margin: 0, valign: "top", isTextBox: true }, o));
// right-hand callout in the style of the examples: "1: heading", big amber number, small text
function callout(s, x, y, w, head, big, desc, bigSize) {
  T(s, head.replace(/^\d+:\s*/, ""), { x, y, w, h: 0.25, fontSize: 12, bold: true });
  let yy = y + 0.27;
  if (big) { T(s, big, { x, y: yy, w, h: 0.5, fontSize: bigSize || 28, bold: true, color: AMB, valign: "middle" }); yy += 0.5; }
  T(s, desc, { x, y: yy, w, h: 0.7, fontSize: 10.5 });
}
// Tables are drawn by make_tables.py (matplotlib) from tables_spec.json, and placed here as images.
const TABLE_SPECS = []; let tcount = 0;
function pngSize(p) { const b = fs.readFileSync(p); return [b.readUInt32BE(16), b.readUInt32BE(20)]; }
function table(s, head, rows, x, y, w, colW, o) {
  o = o || {};
  const id = `s${n}_${++tcount}`;
  TABLE_SPECS.push({ id, head, rows, w, colW, fs: o.fs || 10, rowH: o.rowH || 0.3, hl: Object.keys(o.hl || {}), colors: o.colors || {}, noBold: !!o.noBold });
  const p = `tables/${id}.png`;
  if (!fs.existsSync(p)) return;
  const [pw, ph] = pngSize(p);
  s.addImage({ path: p, x, y, w, h: w * ph / pw });
}
function chartBase(extra) {
  return Object.assign({ catAxisLabelColor: INK, valAxisLabelColor: INK, catAxisLabelFontSize: 10, valAxisLabelFontSize: 10, catAxisLabelFontFace: F, valAxisLabelFontFace: F,
    valGridLine: { color: "E3E3E3", size: 0.5 }, catGridLine: { style: "none" }, showLegend: true, legendPos: "b", legendFontSize: 10, legendColor: INK, legendFontFace: F,
    dataLabelFontSize: 9, dataLabelColor: INK, dataLabelFontFace: F, titleFontFace: F, titleFontSize: 11, titleColor: INK, showTitle: true }, extra);
}
function box(s, x, y, w, h, head, body, col) {
  T(s, head, { x, y, w, h: 0.3, fontSize: 12, bold: true, color: col || ORG, valign: "middle" });
  s.addShape(pres.ShapeType.line, { x, y: y + 0.32, w: w - 0.1, h: 0, line: { color: col || ORG, width: 1.25 } });
  T(s, body, { x, y: y + 0.4, w: w - 0.1, h: h - 0.42, fontSize: 9.5 });
}

// ---------------------------------------------------------------- title
{
  const s = pres.addSlide(); n++;
  s.background = { color: "FFFFFF" };
  s.addImage({ path: "kgp_logo.png", x: 0.7, y: 0.6, w: 1.1, h: 1.23 });
  T(s, "Indian Institute of Technology Kharagpur", { x: 2.0, y: 0.8, w: 7.4, h: 0.4, fontSize: 16, color: GREY, valign: "middle" });
  T(s, "B.Tech Project 2026-27", { x: 2.0, y: 1.2, w: 7.4, h: 0.3, fontSize: 12, color: GREY, valign: "middle" });
  T(s, "Characterising AI-Induced Technical Debt and Its Impact on Software Maintenance", { x: 0.7, y: 2.3, w: 8.6, h: 1.3, fontSize: 28, bold: true, color: INK, valign: "middle" });
  s.addShape(pres.ShapeType.line, { x: 0.7, y: 3.75, w: 1.2, h: 0, line: { color: AMB, width: 2 } });
  T(s, "Souhardya Dandapat", { x: 0.7, y: 3.95, w: 8.6, h: 0.4, fontSize: 16, color: INK, valign: "middle" });
  T(s, "Prioritising technical debt, and testing whether the ranking is any good", { x: 0.7, y: 4.4, w: 8.6, h: 0.3, fontSize: 12, color: GREY, valign: "middle" });
  s.addNotes("Good morning. I am Souhardya Dandapat, and this is my project on AI-induced technical debt and its impact on maintenance. In the next fourteen minutes I will show how I built a dataset to study debt, how I rank debt items, and, mainly, how I test whether the ranking is any good.");
}

// ---------------------------------------------------------------- 1
{
  const s = slide("Why this matters: debt arrives faster than it is repaid",
    "AI-generated code adds debt faster than teams can repay it",
`Good morning. My project is about technical debt, and the question behind it is simple: when a team has more debt than it can repay, what should it fix first?
This matters more now because of AI-generated code. The Stanford AI Index counted 233 reported AI incidents in 2024, 56 percent more than the year before. Veracode found that 45 percent of AI-generated code samples contained a security flaw. And a study of more than 6,000 repositories found that 22.7 percent of the issues introduced by AI-written commits are still in the code at the latest revision.
So code is written faster, debt builds up faster, and nobody can repay all of it. The team has to rank. My work is about building such a ranking, and, mostly, about measuring whether the ranking is any good.`);
  table(s, ["Evidence", "Number", "Source"], [
    ["AI incidents reported in 2024", "233 (+56% on 2023)", "Stanford AI Index 2025 [15]"],
    ["AI-generated code samples with a security flaw", "45%", "Veracode 2025 [16]"],
    ["AI-introduced issues still in the latest revision", "22.7% of 484,366 issues, 6,299 repos", "Liu et al. 2026 [9]"],
    ["Orgs with an AI-model breach that lacked AI access controls", "97%", "IBM 2025 [17]"],
    ["Poor software quality, US cost per year", "US$2.41 trillion", "CISQ 2022 [19]"]],
    0.4, 1.1, 6.0, [2.7, 1.9, 1.4], { rowH: 0.5 });
  T(s, "Percentages come from different studies with different samples; they are not one population. The Veracode figure is specific to its benchmark tasks.", { x: 0.4, y: 4.2, w: 6.0, h: 0.5, fontSize: 9.5, color: GREY });
  callout(s, 6.8, 1.1, 2.8, "1: Debt arrives faster", "22.7%", "of AI-introduced issues are still there at the latest revision [9]");
  callout(s, 6.8, 2.35, 2.8, "2: No one repays everything", "Which first?", "teams must rank, and the ranking has to be defensible", 22);
  callout(s, 6.8, 3.6, 2.8, "3: Nobody can check the ranking", null, "no standard benchmark or metric exists for LLM-era debt [10], and prioritisation research has no validated tools [1]");
}

// ---------------------------------------------------------------- 2
{
  const s = slide("Incidents show what rushed change costs",
    "Reported cases; causes are as reported by the sources, not proven by me",
`Some concrete cases. In December 2025 the Financial Times reported a long AWS outage that followed a change by an AI coding agent. Amazon disputes the AI framing and says it was a misconfigured access role, so I present it as reported, not proven. In 2025 a Replit agent deleted a production database during a code freeze. GitClear measured more duplicated code and less refactoring in the AI period.
What I take from these: failures are cheap to create and expensive to repay, and the question of what to repay first has no validated answer. That is the gap I work on.`);
  table(s, ["Case", "What was reported", "Debt angle"], [
    ["Amazon / AWS, Dec 2025", "~13 h outage after an AI coding-agent change (FT). Amazon: access misconfiguration, not AI", "Review gap"],
    ["Amazon retail, Mar 2026", "Outages and stricter sign-off for AI-assisted changes (wording to be re-checked)", "Review gap"],
    ["Replit agent, Jul 2025", "Agent deleted a production database during a code freeze (AI Incident Database)", "No guardrails"],
    ["GitClear, 2025", "More duplicated code, less refactoring (moved code) in the AI period [18]", "Design debt"],
    ["Poor quality, US, 2022", "US$2.41 trillion per year [19]", "Cost of debt"]],
    0.4, 1.1, 6.2, [1.6, 3.5, 1.1], { rowH: 0.55 });
  callout(s, 6.9, 1.1, 2.7, "1: Where debt hides", "Review gaps", "changes land faster than people can read them", 24);
  callout(s, 6.9, 2.4, 2.7, "2: What is missing", "A ground truth", "a way to say which debt item really cost the most, so rankings can be tested", 20);
  callout(s, 6.9, 3.7, 2.7, "3: My question", null, "does a ranking by predicted cost beat chance, and beat a simple rule?");
}

// ---------------------------------------------------------------- 3-5 literature
function lit(title, caption, rows, spoken) {
  const s = slide(title, caption, spoken);
  table(s, ["Paper", "Venue", "What they studied", "What they found", "What I take from it"], rows, 0.4, 1.05, 9.2, [1.75, 0.85, 1.9, 2.5, 2.2], { rowH: 0.78, fs: 10 });
  return s;
}
lit("Literature 1 of 3: how debt is prioritised and managed", "Prioritisation studies and tooling",
  [["[1] Lenarduzzi, Besker, Taibi, Martini, Arcelli Fontana", "JSS 2021", "Systematic review of 557 papers, 44 primary studies", "Approaches optimise different criteria; no consensus on factors; no validated tools", "Ranking needs measurable criteria and a test"],
   ["[2] Alfayez, Winn, Alwehaibi, Venson, Boehm", "IST 2023", "How teams prioritise SonarQube-found debt (case study)", "Value is subjective and context-dependent; no silver bullet", "Use cost and interest, not opinion of value"],
   ["[3] Baldassarre, Lenarduzzi, Romano, Saarimaki", "IST 2020", "Accuracy of SonarQube remediation time", "Estimates are inaccurate; debt items are spread out", "Build my own time and effort model"],
   ["[4] Biazotto, Feitosa, Avgeriou, Nakagawa", "IST 2024", "Automation of debt management, 178 studies", "121 automation artefacts; integration across them lacking", "End-to-end ranked pipeline"]],
`I read twelve papers in three groups. The first group is about prioritisation itself.
Lenarduzzi and colleagues reviewed 44 primary studies and found no consensus on which factors matter and no validated tools. Alfayez and colleagues looked at how teams prioritise debt that SonarQube found, and the answer was that value is subjective, so there is no silver bullet. Baldassarre and colleagues showed that SonarQube's remediation time is often inaccurate. Biazotto and colleagues mapped 178 studies on automation and found that the pieces are not integrated.
So I need ranking criteria I can measure, and a way to test them.`);
lit("Literature 2 of 3: interest, cost and impact", "Debt as a loan: principal and interest",
  [["[5] Ampatzoglou, Ampatzoglou, Chatzigeorgiou, Avgeriou", "IST 2015", "Financial aspects of debt, systematic review", "Interest is the central idea but hard to measure", "Quantify interest explicitly"],
   ["[6] Digkas, Ampatzoglou, Chatzigeorgiou, Avgeriou, Matei, Heb", "SN CS 2021", "Risk of generating interest (case study)", "A risk metric can prioritise repayment; new code is less risky than legacy", "Rank by an interest-based score"],
   ["[7] Lenarduzzi, Saarimaki, Taibi", "JSS 2020", "SonarQube issues against faults and changes", "Effect is significant but small", "Violation count alone is a weak ranking"],
   ["[12] Wiriyakul, Senivongse", "2025", "Interest of code-smell debt from release history", "Interest is rework inside a persisting smell, converted with COCOMO II", "My interest method (person-months)"]],
`The second group is about interest, the extra cost that debt causes while it stays. Ampatzoglou and colleagues say interest is the central idea but hard to measure. Digkas and colleagues propose an interest-risk metric that can help prioritise repayment. Lenarduzzi and colleagues found that SonarQube rule violations have only a small effect on faults and changes, so counting violations is a weak way to rank.
And the method I actually implemented is from Wiriyakul and Senivongse: interest is the rework done inside a code smell that persists, and you convert those lines to effort with COCOMO II. That gives interest in person-months.`);
lit("Literature 3 of 3: AI-era debt, benchmarks and detection", "Where data with a known answer comes from",
  [["[9] Liu, Widyasari, Zhao, Irsan, Chen, Lo", "arXiv 2026", "302.6k AI-authored commits, 6,299 repositories", "484,366 issues, 89.3% code smells; 22.7% still present", "AI debt persists, so ranking is needed"],
   ["[10] Ehsani, Rawal, Cai, Chatterjee", "arXiv 2026", "Multivocal review, 104 sources, LLM-assisted development", "New LLM-specific debt kinds; no standard benchmark or metric", "A benchmark with known answers is missing"],
   ["[11] Lin et al. (SmellBench)", "arXiv 2026", "Smells injected into clean real code", "294 cases, 7 smell types, human-written ground truth", "Injection idea, at whole-project level"],
   ["[8] Li, Soliman, Avgeriou", "EMSE 2023", "Self-admitted debt from four sources", "F1 0.611 over 4 SATD types; 103 projects", "SATD comments as features"]],
`The third group is the AI era and data. Liu and colleagues studied 302 thousand AI-written commits and found 484 thousand issues, mostly code smells, with 22.7 percent still present. Ehsani and colleagues reviewed 104 sources and found new kinds of debt specific to LLM use, and no standard benchmark. SmellBench injects smells into clean real code so that every case has a known answer. Li and colleagues detect self-admitted debt from four sources.
The missing piece is a benchmark where the debt type, the cost and the future interest are known. I follow the injection idea, but with whole projects, five debt types and a time label.`);

// ---------------------------------------------------------------- 6 architecture
{
  const s = slide("What I built, at one glance", "From data creation to the evaluation of the ranking",
`This is the whole work on one slide, left to right.
First, data creation: ten open-source projects, a clean and a debt copy of each, three injected bugs, and separately the git history of nine real projects. Second, the characteristics: every project becomes 133 numbers, plus a fix-time number, and every debt instance in the history gets an interest in person-months. Third, two prediction models. Level one says what kind of debt a change introduces. Level two says which debt instance will absorb future work. Fourth, what comes out: a debt-type and cost ranking, and an instance ranking. And fifth, the evaluation, which is the main goal: protocols that avoid leakage, and measures that compare the ranking with random, a simple rule and a perfect order.`);
  s.addImage({ path: "figs/architecture.png", x: 0.4, y: 1.0, w: 9.2, h: 3.75 });
  T(s, "Main goal of the study: not only to rank debt, but to measure how good the ranking is.", { x: 0.4, y: 4.85, w: 9.2, h: 0.4, fontSize: 13, bold: true, color: INK });
}

// ---------------------------------------------------------------- 7 dataset creation
{
  const s = slide("Dataset creation: 61 pairs of clean and debt projects", "Built from scratch: the steps and the reason for each",
`Now how I built the dataset. A snippet cannot show an import cycle or tight coupling, so each data point is a pair of whole projects: a clean one and one with a single injected debt.
I took ten open-source projects with working tests: boltons, click, jinja and werkzeug in Python, and C-Thread-Pool, cJSON, jansson, libpng, libyaml and zlib in C. For each pair I made one small change that introduces a debt of one of five types, so the type, the place and the clean twin are known. Sixty are injected, 45 by scripts and 15 written in the SmellBench style, and one is a real libpng fix.
Both copies must pass the project's own tests, because real debt does not break the program. Then the audit: I asked whether a one or two line change is really debt. A pair stays only if a metric of its own type moved. Of 102 candidates, 52 stayed. I then added nine pairs from two more projects and got 61. Finally three bugs per pair, with the same patch on both sides, to get a fix-time difference.`);
  table(s, ["Step", "What I did", "Why"], [
    ["Projects", "10 open-source projects with test suites; 4 Python, 6 C/C++", "whole projects hold structure that snippets cannot show (cycles, fan-in/out)"],
    ["Inject", "one small change per pair, 5 types; 60 injected (45 scripted, 15 SmellBench-style [11]) and 1 natural fix (libpng)", "known type and place, and a clean twin to compare against"],
    ["Keep working", "debt copy must pass the project's own tests", "real debt does not break behaviour"],
    ["Audit", "keep a pair only if a metric of its own type moved: 52 of 102 kept", "a 1-2 line change must be visible as debt, not just assumed"],
    ["Add", "C-Thread-Pool (4) and libyaml (5): total 61", "more concurrency and security cases in C"],
    ["Bugs", "3 mutations per pair, same patch on both copies: 183", "gives a fix-time difference that comes from the debt"]],
    0.4, 1.05, 6.3, [0.95, 3.0, 2.35], { rowH: 0.52, fs: 9.5 });
  s.addImage({ path: "figs/funnel.png", x: 6.9, y: 1.0, w: 2.8, h: 2.3 });
  callout(s, 6.9, 3.4, 2.7, "50 of 102 dropped", null, "no metric of the pair's own type moved. It means 'not visible to these metrics', not 'not debt'");
  callout(s, 6.9, 4.3, 2.7, "60 + 1", null, "injected + natural. Natural debt is future work");
}

// ---------------------------------------------------------------- 8 dataset features
{
  const s = slide("Dataset curated so far: 61 datapoints, 133 features", "Every column of out_dataset; the vector of a project, and delta = debt copy minus clean copy",
`This is the dataset as it stands. Each row is one pair, and the model sees the difference between the debt copy and the clean copy, 133 numbers in three blocks.
Structure, 46 numbers: the directory layout, and the import or include graph, with fan-in, fan-out, cycles, density, modularity and a few spectral values. Code, 50 numbers: size, comments, function length, cyclomatic complexity, parameters, and language idioms. Technical debt, 37 numbers: smells and their COCOMO principal, class cohesion, concurrency idioms such as locks and threads, duplication, security findings and validation guards, and self-admitted debt in comments.
Plus one time number, and the target is the debt type. On the right you see the types by language: concurrency and security dominate, boltons gives 24 pairs, all concurrency. Remember that, it comes back in the results.`);
  table(s, ["Block", "n", "Feature families (what is measured)"], [
    ["Structure", "46", "layout: files, dirs, depth, file-size spread, Gini, header/init share (13). Dependency graph: nodes, edges, density, cycles, fan-in/out, instability, dependency depth, clustering, modularity, PageRank, 6 spectral values (33)"],
    ["Code", "50", "size and comments (11); function length, CCN, parameters, tokens (20); Python idioms: classes, docstrings, try/except, lambda (11); C idioms: malloc/free, goto, casts, asserts (8)"],
    ["Debt", "37", "long / complex / many-parameter methods and COCOMO principal (15); class cohesion LCOM4 (4); concurrency: locks, threads, atomics, shared globals (6); security findings, guards (3); self-admitted debt (7); duplication (2)"],
    ["Time", "1", "time_diff_min (minutes), only in the with-time file"],
    ["Target", "1", "td_type (5 classes: complexity, concurrency, coupling, dependency, security)"]],
    0.4, 1.05, 5.9, [0.8, 0.4, 4.7], { rowH: 0.55, fs: 8.5 });
  T(s, "Layouts: delta_only = 133 columns; full = clean__, td__, delta__ = 399 columns. Folds: stratified, and by project. 0 missing values, 0 infinite values, 0 pairs with identical vectors.", { x: 0.4, y: 4.8, w: 5.9, h: 0.45, fontSize: 9, color: GREY });
  const labels = ["concurrency", "security", "dependency", "coupling", "complexity"];
  s.addImage({ path: "figs/types_language.png", x: 6.5, y: 1.0, w: 3.2, h: 2.6 });
  callout(s, 6.6, 3.7, 3.0, "Project and type are tangled", "24 of 26", "concurrency pairs come from one project (boltons)", 24);
}

// ---------------------------------------------------------------- 9 bugs and time
{
  const s = slide("Bugs and the fix-time label", "Why there is a time number at all, how it was made, and what it can show",
`Why a time number? The point of debt is that later work gets slower. So I took the same bug and fixed it in the clean copy and in the debt copy; the extra time in the debt copy is the cost of the debt. Three bugs per pair, 183 in total, made by small mutations such as flipping a comparison or an off-by-one, with the identical patch on both copies.
Now the honest part. I could not have developers fix 183 bugs on 122 project versions, so the times come from a ground-truth time model with assumed factors per debt type: concurrency 3.4 times slower, security 2.4, complexity 1.8, coupling 1.4, dependency 1.05. The chart shows the resulting extra minutes per pair. I set these factors after seeing how the classifiers behaved, and time alone predicts the type with 0.93 accuracy. So the time feature is almost a label. Any gain from it depends on this model; it is not evidence about real developers. The plan is to replace it with measured times.`);
  T(s, [{ text: "How a bug is made", options: { bold: true, breakLine: true } },
    { text: "mutation kinds: negate condition (58), const off-by-one (35), arithmetic (27), bool operator (23), equality (23), boundary (17)", options: { bullet: true, breakLine: true } },
    { text: "the same patch goes into the clean and the debt copy: 183 bugs, 70 of them in a file the debt change touched", options: { bullet: true, breakLine: true } },
    { text: "checked: all 246 bugged Python files parse; 59 of 59 C files pass a syntax compile; re-running gives identical patches", options: { bullet: true, breakLine: true } },
    { text: "not checked: that each bug makes a test fail", options: { bullet: true, color: RED } }],
    { x: 0.4, y: 1.05, w: 5.2, h: 1.9, fontSize: 10.5, paraSpaceAfter: 3 });
  table(s, ["Debt type", "Slowdown factor", "Mean extra minutes per pair"], [
    ["concurrency", "3.4", "161.6"], ["security", "2.4", "92.0"], ["complexity", "1.8", "53.5"], ["coupling_cohesion", "1.4", "22.7"], ["dependency_structure", "1.05", "3.2"]],
    0.4, 3.0, 5.2, [2.0, 1.4, 1.8], { rowH: 0.3, fs: 10 });
  s.addImage({ path: "figs/fix_time.png", x: 5.9, y: 1.0, w: 3.8, h: 2.5 });
  callout(s, 6.0, 3.65, 3.6, "Time alone predicts the type", "0.93", "accuracy of the time column by itself. The factors were set after seeing the classifiers, so any gain from time is conditional on this time model", 26);
}

// ---------------------------------------------------------------- 10 classifier architecture
{
  const s = slide("Level 1: debt-type classifier, architecture, metrics", "Seven classifiers compared; final model is the 10-best-features selector followed by a random forest",
`Level one answers: given the difference vector of a pair, which of the five debt types was introduced. The pipeline on top is the final model: the 133 delta features plus time go in, a selector keeps the ten best features by ANOVA F, and a random forest with 300 trees and balanced class weights gives the type.
Why a selector? I have 61 rows and 134 columns, so a model drowns in noise. The key point is that the selector is fitted inside each training fold, so the test fold never decides which features are kept. That avoids leakage.
I compared seven classifiers to see whether the time effect depends on the algorithm. Because classes are unequal, 26, 16, 7, 6 and 6, I report accuracy and macro F1, and balanced accuracy, and compare with a majority baseline of 0.426. To test whether the gain from time is real I use a McNemar test on the same predictions and a bootstrap interval for the difference. I ran 656 experiments in total, with nothing tuned on a test fold.`);
  const bx = [[0.4, "133 delta features + time", "input vector of a pair"], [2.7, "SelectKBest, k = 10", "ANOVA F, inside each training fold"], [5.0, "Random forest [24]", "300 trees, balanced class weights"], [7.3, "Debt type", "5 classes"]];
  s.addImage({ path: "figs/level1_flow.png", x: 0.4, y: 1.0, w: 9.2, h: 0.8 });
  table(s, ["Classifier", "Setting (fixed, not tuned)", "Why it is in the comparison"], [
    ["Random forest [24]", "300 trees, balanced", "strong default for small tables"],
    ["Gradient boosting [25]", "100 trees, depth 2", "boosted alternative"],
    ["Logistic regression", "standardised, C=1, balanced", "linear check"],
    ["SVM (RBF)", "standardised, C=3, balanced", "margin-based check"],
    ["kNN", "k=3, standardised", "distance-based, no training"],
    ["10-best + RF / LR", "SelectKBest k=10 in folds", "61 rows for 133 features: cut noise"],
    ["Majority; time only", "baselines", "floor; is time a label?"]],
    0.4, 1.85, 6.1, [1.6, 2.1, 2.4], { rowH: 0.33, fs: 9.5 });
  callout(s, 6.8, 1.85, 2.8, "1: Metrics", null, "accuracy, macro-F1 (classes 26/16/7/6/6), balanced accuracy. Baseline: majority = 0.426");
  callout(s, 6.8, 2.85, 2.8, "2: Is a gain real?", null, "McNemar test [21] on the same predictions; bootstrap 95% CI [22] of the accuracy difference");
  callout(s, 6.8, 3.85, 2.8, "3: Scale", "656", "runs: 7 models x 2 layouts x 4 protocols x with/without time (scikit-learn [23])", 24);
}

// ---------------------------------------------------------------- 11 protocols
{
  const s = slide("Why four protocols, and how each is used", "Each protocol answers a different question and guards against a different leak",
`Why four protocols? Because the pairs of one project look alike. In boltons, 24 pairs are all concurrency, so if one boltons pair is in training and another in testing, the model can just recognise the project and guess the type.
The first two protocols, stratified folds and 20 repeated random stratified splits, keep the type proportions. They are the optimistic ones, and the repeated one gives a stable average with a spread. The last two hold out whole projects: project folds, where a project is in one fold only, and leave-one-project-out, where each of the ten projects is tested once after training on the other nine. These tell the truth about unseen projects, and that is where accuracy drops.
So I report all four, and I read the strict ones as the honest result.`);
  table(s, ["Protocol", "How the data is split", "Why I use it", "What it guards against"], [
    ["Given stratified", "5 folds, each keeps the type proportions", "same splits for every model, so differences are comparable", "a fold missing a rare type"],
    ["20 random stratified", "20 repeats of a 5-fold stratified split", "average and spread over many splits", "one lucky split"],
    ["Given by project", "5 folds; a project sits in one fold only", "tests projects the model never saw", "project fingerprint leak"],
    ["Leave one project out", "10 folds; each project held out once", "strictest test of generalisation", "project fingerprint leak, fully"]],
    0.4, 1.05, 6.4, [1.35, 1.8, 1.9, 1.35], { rowH: 0.6, fs: 9 });
  T(s, [{ text: "How I read them: ", options: { bold: true } }, { text: "the first two are optimistic because pairs of one project are in both train and test. The last two are the honest numbers for new projects." }], { x: 0.4, y: 4.45, w: 6.4, h: 0.6, fontSize: 10.5 });
  callout(s, 7.1, 1.05, 2.5, "1: Leakage is likely", "24", "boltons pairs, all concurrency: the model can learn the project", 28);
  callout(s, 7.1, 2.35, 2.5, "2: Debt change is small", "0.008", "mean |delta| in std units: projects differ far more than debt", 24);
  callout(s, 7.1, 3.7, 2.5, "3: Selection inside folds", null, "the 10 features are chosen on training data only");
}

// ---------------------------------------------------------------- 12 interest method
{
  const s = slide("Level 2: interest in person-months from git history", "Method of Wiriyakul and Senivongse [12] with COCOMO II [13]; implemented on 9 real projects, 20 releases each",
`Level two works on real projects, because the injected pairs have no later history and so no real interest. I follow the 2025 method.
Take the last 20 release tags. A debt instance is a SonarQube issue for Python, and for C and C++ a structural smell: a method longer than 50 lines, complexity above 10, or more than five parameters, because the free SonarQube has no C or C++ analyser. The region of an instance is its function. Between two releases, git diff tells me the lines changed inside that function.
If the instance disappeared, that is repayment. If it is new, or the function grew, the principal increased. If it persists, the other changed lines are interest. COCOMO II turns those lines into person-months: 2.94 times thousands of lines to the power 1.0997. Example: 100 changed lines is 0.234 person-months, but ten events of ten lines is 0.186, which is why I compute effort per event.
Result: 10.52 person-months of interest over nine projects, around 6 percent of the effort to rewrite all debt once. Effort multipliers are one, so this is a relative estimate, not measured developer time.`);
  T(s, "PM = A x (lines / 1000)^E     A = 2.94, E = 1.0997 (COCOMO II.2000 nominal)", { x: 0.4, y: 1.05, w: 6.0, h: 0.3, fontSize: 12, bold: true, color: AMB });
  table(s, ["Between two releases", "Counted as", "How"], [
    ["Instance disappears", "Repayment", "principal removed"],
    ["Instance is new", "Principal increase", "size of its function"],
    ["Persists, function grows", "Principal increase", "added lines of the growth"],
    ["Persists, other changed lines", "Interest", "git diff -U0, inside the function"]],
    0.4, 1.45, 6.0, [2.1, 1.5, 2.4], { rowH: 0.36, fs: 10 });
  T(s, [{ text: "Worked example. ", options: { bold: true } }, { text: "100 interest lines in one event: 2.94 x 0.1^1.0997 = 0.234 person-months. The same 100 lines as 10 events of 10 lines: 10 x 2.94 x 0.01^1.0997 = 0.186. E > 1 makes one big change cost more than many small ones." }], { x: 0.4, y: 3.55, w: 6.0, h: 0.7, fontSize: 10.5 });
  T(s, "Instances: SonarQube issues (Python); structural smells (C/C++): method > 50 lines, CCN > 10, > 5 parameters (lizard). C-Thread-Pool has no release tags, so 9 of the 10 projects are used. Multipliers = 1: relative estimate.", { x: 0.4, y: 4.5, w: 6.0, h: 0.7, fontSize: 9, color: GREY });
  callout(s, 6.8, 1.05, 2.8, "1: Total interest", "10.52 PM", "9 projects (0.09 to 2.44 each)", 26);
  callout(s, 6.8, 2.25, 2.8, "2: Compared with principal", "~6%", "of the effort to rewrite all debt once", 26);
  callout(s, 6.8, 3.45, 2.8, "3: Data", "20,853", "instance-releases, 1,557 instances, 1,607 interest events", 26);
}

// ---------------------------------------------------------------- 13 interest models and evaluation design
{
  const s = slide("Level 2: interest models and ranking evaluation", "Rank the instances of one release by predicted interest; check against what happened in the next release",
`Now the models for interest, and how I evaluate them. Each row is one debt instance in one release. Features are its age, interest paid so far, number of events, function size and complexity. I tried three targets: whether any interest happens in the next release, how many person-months, and a two-part hurdle model that combines both, as in count-data models.
The evaluation is the core of the work. In each repository and release I rank the instances by predicted interest and look at what really happened next. Capture at k is the share of all real interest that falls in my top k percent. A random ranking captures k percent. Lift says how much more likely the top items are to pay interest than a random pick. NDCG rewards putting the biggest ones first.
Baselines: random, which is also what the zero model gives; persistence, which ranks by interest already paid, the simple rule a manager could use; and the oracle, the best possible order. Uncertainty comes from a bootstrap over 2,000 resamples of the groups. I use two protocols: leave-one-repo-out, 123 groups, and a temporal split, 57 groups, training on earlier releases.`);
  table(s, ["Target", "Model", "Question"], [
    ["Any interest next release", "random forest classifier", "will it absorb work?"],
    ["Amount (person-months)", "random forest regressor", "how much?"],
    ["Both", "two-part (hurdle) model [27]", "will it, and then how much"]],
    0.4, 1.05, 5.8, [1.9, 2.0, 1.9], { rowH: 0.28, fs: 9.5 });
  table(s, ["Measure", "What it tells"], [
    ["Capture@k", "share of the real next-release interest inside my top k%"],
    ["Precision@k, lift", "do the top k% really pay interest, relative to the base rate"],
    ["NDCG@20 [26]", "is the order right, weighted by amount"],
    ["Bootstrap CI", "95% interval over repo-release groups (2,000 draws)"]],
    0.4, 2.45, 5.8, [1.5, 4.3], { rowH: 0.28, fs: 9.5 });
  table(s, ["Baseline", "Role"], [
    ["Random / zero model", "lower bound (zero model = random order)"],
    ["Persistence", "rank by interest already paid"],
    ["Oracle", "upper bound: sort by the true value"]],
    0.4, 4.15, 5.8, [1.8, 4.0], { rowH: 0.26, fs: 9.5 });
  callout(s, 6.6, 1.05, 3.0, "1: Unit of ranking", "repo x release", "one repository at one release (>= 10 instances, some real interest)", 22);
  callout(s, 6.6, 2.4, 3.0, "2: Protocols", "123 | 57", "groups: leave-one-repo-out | temporal (train on earlier releases)", 26);
  callout(s, 6.6, 3.65, 3.0, "3: Hard part", "92%", "of instance-releases have zero interest, so amounts are heavy-tailed", 26);
}

// ---------------------------------------------------------------- 14 result 1
{
  const s = slide("Result 1: debt type, with and without fix time", "Final model: 10-best features + random forest, delta_only layout; accuracy",
`Results. On the left, the final model with and without the time feature, for the four protocols. With stratified folds accuracy goes from 0.79 to 0.92, with 20 random splits from 0.84 to 0.94. For the stratified case the confidence interval of the gain is 0.05 to 0.23 and McNemar gives p equal to 0.008.
On the right, the seven classifiers on the same splits. Only the models with the selector gain a lot. The plain random forest is already at 0.885 without time and does not move. My reading, which I have not tested separately, is that time is the top-ranked feature, so the selector always keeps it, while the forest mixes it with 133 weaker ones.
And please note the last two bars on the left: with unseen projects accuracy falls to 0.43 without time, the same as always guessing concurrency, and 0.51 with time. So the model does not generalise across projects yet.`);
  const cats = ["Stratified", "20 random", "By project", "Leave-1-project-out"];
  s.addImage({ path: "figs/acc_protocol.png", x: 0.3, y: 0.95, w: 4.7, h: 2.95 });
  const mc = ["10-best + RF", "10-best + LR", "kNN", "SVM (RBF)", "Logistic reg.", "Grad. boosting", "Random forest"];
  s.addImage({ path: "figs/acc_classifiers.png", x: 5.0, y: 0.95, w: 4.7, h: 2.95 });
  callout(s, 0.4, 4.0, 2.9, "1: Time helps the selector model", "+0.13", "0.79 to 0.92; 95% CI +0.05 to +0.23; McNemar p = 0.008", 24);
  callout(s, 3.5, 4.0, 3.0, "2: Plain forest does not gain", "0.885", "with and without time. Time is the top feature (F = 120), so the selector keeps it", 24);
  callout(s, 6.7, 4.0, 3.0, "3: New projects: weak", "0.43", "without time = majority baseline (0.426); 0.51 with time", 24);
}

ni++; // notes entry of the removed controls slide

// ---------------------------------------------------------------- 16 result 3 capture bars
{
  const s = slide("Result 3: ranking instances by predicted interest", "Share of next-release interest captured in the top k% of the ranking; leave-one-repo-out, 123 repo-release groups",
`This is the main result. For every repository and release I ranked the debt instances and looked at how much of the interest of the next release falls into the top 10, 20 and 30 percent.
Random captures 10, 20 and 30. The two-part model captures 38.5 percent in the top 20, with a confidence interval from 32 to 44, about 1.9 times random. A perfect order would capture 95.8. The zero model, which predicts nothing, lands on random, as it should.
But the simple rule, rank by interest already paid, captures 38.8 percent. So my learned models are clearly better than chance, and I cannot show that they beat that simple rule at this budget. The temporal protocol shows the same picture, with intervals that overlap. NDCG is only 0.21, so the order inside the top group is weak.`);
  const g = m => [P[`leave-one-repo-out|${m}`].cap10, P[`leave-one-repo-out|${m}`].cap20, P[`leave-one-repo-out|${m}`].cap30];
  const lab = ["Top 10%", "Top 20%", "Top 30%"];
  s.addImage({ path: "figs/capture_bars.png", x: 0.3, y: 0.95, w: 5.6, h: 2.9 });
  const H = P["leave-one-repo-out|hurdle_rf"], Pe = P["leave-one-repo-out|persistence"], R = P["leave-one-repo-out|rf_pm"], Z = P["leave-one-repo-out|zero"];
  const f = x => (x * 100).toFixed(1) + "%";
  table(s, ["Model, top 20%", "Capture (95% CI)", "Lift", "NDCG@20"], [
    ["Zero model (= random)", f(Z.cap20), Z.lift20.toFixed(2), Z.ndcg20.toFixed(2)],
    ["Persistence", `${f(Pe.cap20)} (${(Pe.cap20_lo * 100).toFixed(0)}-${(Pe.cap20_hi * 100).toFixed(0)})`, Pe.lift20.toFixed(2), Pe.ndcg20.toFixed(2)],
    ["RF regression", `${f(R.cap20)} (${(R.cap20_lo * 100).toFixed(0)}-${(R.cap20_hi * 100).toFixed(0)})`, R.lift20.toFixed(2), R.ndcg20.toFixed(2)],
    ["Two-part model", `${f(H.cap20)} (${(H.cap20_lo * 100).toFixed(0)}-${(H.cap20_hi * 100).toFixed(0)})`, H.lift20.toFixed(2), H.ndcg20.toFixed(2)]],
    0.4, 3.95, 5.5, [1.8, 1.8, 0.8, 1.1], { rowH: 0.27, fs: 9.5, hl: { "3,1": "FDE9D0" } });
  callout(s, 6.3, 1.0, 3.3, "1: Beats chance", "38.5%", "of next-release interest in the top 20% (95% CI 32-44%); random gives 20%, about 1.9x", 28);
  callout(s, 6.3, 2.3, 3.3, "2: Not better than a simple rule", "38.8%", "persistence (rank by interest already paid) in the same top 20%", 28);
  callout(s, 6.3, 3.6, 3.3, "3: Room left", "95.8%", "oracle at top 20%. Spearman rho only 0.14, so the order inside the top is weak", 28);
}

// ---------------------------------------------------------------- 17 result 4 curve
{
  const s = slide("Result 4: capture curve and the simple rule", "Average capture when a team fixes the top k% of instances; leave-one-repo-out",
`The bars showed three points. This is the whole curve: if a team could repay the top k percent, how much of the future interest do they catch. The diagonal is random, the top line is the oracle.
All three methods sit well above random. Persistence is slightly ahead at the very top, the first 5 to 10 percent, but the two-part model pulls ahead for larger budgets. At 50 percent, the model captures 73.5 percent against 67.0 for persistence. I tested that difference with a paired bootstrap over the 123 groups: plus 5.6 points, interval 0.4 to 10.7, so it is positive but marginal, and I looked at several k, so I would not oversell it. At 20 percent the difference is minus 2 points with an interval that includes zero.
Honest reading: the model adds something for larger budgets, nothing demonstrated for small ones.`);
  const ks = CV.k.map(String);
  s.addImage({ path: "figs/capture_curve.png", x: 0.3, y: 0.95, w: 6.0, h: 3.9 });
  const at = (m, k) => (CV[m][CV.k.indexOf(k)] * 100).toFixed(1);
  table(s, ["k", "Rand.", "Pers.", "RF", "Two-part", "Oracle"], [10, 20, 30, 50].map(k => [k + "%", k + ".0", at("persistence", k), at("rf_pm", k), at("hurdle_rf", k), at("oracle", k)]),
    6.5, 1.0, 3.2, [0.4, 0.5, 0.5, 0.45, 0.7, 0.65], { rowH: 0.27, fs: 9, hl: { "3,4": 1, "3,2": 1 } });
  T(s, "Capture in % of next-release interest", { x: 6.5, y: 2.45, w: 3.2, h: 0.2, fontSize: 8.5, color: GREY });
  table(s, ["k", "Two-part - persistence", "95% CI"], [
    ["10%", "-2.0 pts", "-7.0 to +2.8"], ["20%", "-2.2 pts", "-7.4 to +3.0"], ["30%", "+3.3 pts", "-2.2 to +8.9"], ["50%", "+5.6 pts", "+0.4 to +10.7"]],
    6.5, 2.75, 3.2, [0.5, 1.5, 1.2], { rowH: 0.27, fs: 9, hl: { "3,0": 1, "3,1": 1, "3,2": 1 } });
  T(s, "Paired bootstrap, 123 groups, 3,000 draws. Several k examined: marginal evidence.", { x: 6.5, y: 4.15, w: 3.2, h: 0.3, fontSize: 8, color: GREY });
  T(s, "1: Small budgets: persistence is as good as, or better than, the model", { x: 6.5, y: 4.5, w: 3.2, h: 0.4, fontSize: 10, bold: true });
  T(s, "2: Large budgets: model 73.5% vs 67.0% at k = 50% (marginal)", { x: 6.5, y: 4.95, w: 3.2, h: 0.4, fontSize: 10, bold: true });
}

// ---------------------------------------------------------------- 18 result 5 predictability
{
  const s = slide("Result 5: what can and cannot be predicted", "Leave-one-repo-out and temporal protocols; chance AUC = 0.5",
`Last result: what can the interest models actually predict? Whether an instance will absorb any work in the next release is weakly predictable, with AUC 0.59 on unseen repositories and 0.71 on later releases. A function-level model on the next 100 commits gives 0.57 and 0.62. Weak, but above chance.
How many person-months is not predictable per instance: no regression model beats simply predicting zero, because about 92 percent of instance-releases have no interest at all and the rest is heavy-tailed. The two-part model predicts the project total at 1.14 times the actual, so it is useful to budget a portfolio but not to size single items.
So, in one line: ranking is possible, amount estimation is not.`);
  s.addImage({ path: "figs/auc.png", x: 0.3, y: 0.95, w: 4.7, h: 2.9 });
  table(s, ["Task", "Result", "Verdict"], [
    ["Any interest next release (AUC)", "0.59 / 0.71", "weak, real"],
    ["Amount per instance (PM)", "R2 <= 0; no gain over zero model", "no"],
    ["Project total interest", "predicted / actual = 1.14", "portfolio only"],
    ["Total of a project, next release", "best R2 = -0.14", "no"],
    ["Function, next 100 commits (AUC)", "0.57 / 0.62", "weak"]],
    5.2, 1.05, 4.4, [1.9, 1.7, 0.8], { rowH: 0.45, fs: 9.5, noBold: false });
  callout(s, 0.4, 4.0, 4.5, "1: Ranking is possible", null, "any-interest signal is weak but real and gives the 1.9x capture of Result 3");
  callout(s, 5.3, 4.0, 4.3, "2: Amounts are not", null, "92% zeros and heavy tails; the interest of the injected pairs is undefined (no later history)");
}

// ---------------------------------------------------------------- 19 limits and next steps
{
  const s = slide("Limits, and what comes next", "What I would not claim yet, and the plan to close each gap",
`To close. What I cannot claim yet: that my learned ranking beats the simple history rule; that the time gain holds for real developers; that the type classifier works on unseen projects; or that injected debt behaves like natural debt. Sixty of the 61 pairs are injected, the bugs were checked by parsing, not by tests, and the COCOMO multipliers are not calibrated, so person-months are relative.
Next steps. One: collect real fix times and redo the type result. Two: add features that carry change-proneness, ownership and test coverage, to try to beat persistence. Three: add a cost-aware metric, effort saved when repaying the top k instead of random items. Four: more projects and languages and a calibrated COCOMO. Five: test whether the ranking transfers to AI-generated code, which is where I started.
So the status is: a working, reproducible way to build and evaluate a prioritisation, with a ranking that beats chance and is not yet better than a simple rule. Thank you.`);
  table(s, ["Limit", "Detail", "Next step"], [
    ["Injected debt", "60 of 61 pairs injected; 1 natural (libpng)", "more natural pairs"],
    ["Small data", "61 pairs, classes 26/16/7/6/6; CIs about +-0.10", "more pairs and projects"],
    ["No generalisation yet", "unseen projects 0.43-0.51 accuracy", "richer features; more projects"],
    ["Persistence not beaten", "38.5% vs 38.8% at top 20%", "change-proneness, ownership, tests"],
    ["Effort is relative", "COCOMO multipliers = 1; constants of [12] unchecked", "calibrate; cost-aware metric"],
    ["Bugs not test-validated", "parse / compile checks only", "run the project tests on bugged copies"],
    ["AI-generated code", "motivation, not yet tested", "apply the ranking to AI-written changes"]],
    0.4, 1.05, 9.2, [1.7, 4.4, 3.1], { rowH: 0.45, fs: 10 });
}

// ---------------------------------------------------------------- references
const r1 = [
 "[1] V. Lenarduzzi, T. Besker, D. Taibi, A. Martini, F. Arcelli Fontana. A systematic literature review on technical debt prioritization: strategies, processes, factors, and tools. J. Syst. Softw. 171 (2021) 110827.",
 "[2] R. Alfayez, R. Winn, W. Alwehaibi, E. Venson, B. Boehm. How SonarQube-identified technical debt is prioritized: an exploratory case study. Inf. Softw. Technol. 156 (2023) 107147.",
 "[3] M. T. Baldassarre, V. Lenarduzzi, S. Romano, N. Saarimaki. On the diffuseness of technical debt items and accuracy of remediation time when using SonarQube. Inf. Softw. Technol. 128 (2020) 106377.",
 "[4] J. P. Biazotto, D. Feitosa, P. Avgeriou, E. Y. Nakagawa. Technical debt management automation: state of the art and future perspectives. Inf. Softw. Technol. 167 (2024) 107375.",
 "[5] A. Ampatzoglou, A. Ampatzoglou, A. Chatzigeorgiou, P. Avgeriou. The financial aspect of managing technical debt: a systematic literature review. Inf. Softw. Technol. 64 (2015) 52-73.",
 "[6] G. Digkas, A. Ampatzoglou, A. Chatzigeorgiou, P. Avgeriou, O. Matei, R. Heb. The risk of generating technical debt interest: a case study. SN Comput. Sci. 2 (2021) 12.",
 "[7] V. Lenarduzzi, N. Saarimaki, D. Taibi. Some SonarQube issues have a significant but small effect on faults and changes. J. Syst. Softw. 170 (2020) 110750.",
 "[8] Y. Li, M. Soliman, P. Avgeriou. Automatic identification of self-admitted technical debt from four different sources. Empir. Softw. Eng. 28 (2023) 65.",
 "[9] Y. Liu, R. Widyasari, Y. Zhao, I. C. Irsan, J. Chen, D. Lo. Debt behind the AI boom: a large-scale empirical study of AI-generated code in the wild. arXiv:2603.28592, 2026.",
 "[10] R. Ehsani, S. Rawal, Y. Cai, P. Chatterjee. Faster code, deeper debt? A multivocal literature review on technical debt and its early signs in LLM-assisted software development. arXiv:2606.14796, 2026.",
 "[11] F. Lin, B. Hu, X. Zhu, Z. Zhao, Z. Zheng, Z. Liu, Z. Zhang, J. Zhou, T. Xu. SmellBench: towards fine-grained evaluation of code agents on refactoring tasks. arXiv:2606.05574, 2026.",
 "[12] Wiriyakul, Senivongse. Technical debt interest of code smells from release history with COCOMO II, 2025. Full citation to be added."];
const r2 = [
 "[13] B. Boehm et al. Software Cost Estimation with COCOMO II. Prentice Hall, 2000.",
 "[14] J. Sliwerski, T. Zimmermann, A. Zeller. When do changes induce fixes? MSR 2005 (SZZ bug mining).",
 "[15] Stanford HAI. AI Index Report 2025.     [16] Veracode. 2025 GenAI Code Security Report.     [17] IBM. Cost of a Data Breach Report 2025.",
 "[18] GitClear. AI Copilot Code Quality, 2025.     [19] CISQ. The Cost of Poor Software Quality in the US, 2022.",
 "[20] Financial Times, Dec 2025, report on the AWS outage and the Kiro agent (Amazon disputes the AI cause); AI Incident Database, Replit agent database deletion, Jul 2025.",
 "[21] Q. McNemar. Note on the sampling error of the difference between correlated proportions or percentages. Psychometrika 12 (1947) 153-157.",
 "[22] B. Efron. Bootstrap methods: another look at the jackknife. Ann. Stat. 7 (1979) 1-26.",
 "[23] F. Pedregosa et al. Scikit-learn: machine learning in Python. J. Mach. Learn. Res. 12 (2011) 2825-2830.",
 "[24] L. Breiman. Random forests. Mach. Learn. 45 (2001) 5-32.",
 "[25] J. H. Friedman. Greedy function approximation: a gradient boosting machine. Ann. Stat. 29 (2001) 1189-1232.",
 "[26] K. Jarvelin, J. Kekalainen. Cumulated gain-based evaluation of IR techniques. ACM Trans. Inf. Syst. 20 (2002) 422-446.",
 "[27] J. Mullahy. Specification and testing of some modified count data models. J. Econometrics 33 (1986) 341-365.",
 "Tools: SonarQube Community, lizard (complexity), bandit and flawfinder (security), git; datasets: SmellBench-style projects [11], CppSATD replication package."];
[["References 1 of 2", r1], ["References 2 of 2", r2]].forEach(([t, r]) => {
  const s = slide(t, null, null);
  s.addNotes("Reference slide, not spoken. [15]-[20] are secondary sources for the motivation numbers; check each figure against the original before presenting.");
  T(s, r.map((x, i) => ({ text: x, options: { breakLine: i < r.length - 1 } })), { x: 0.4, y: 0.85, w: 9.2, h: 4.4, fontSize: 9.5, paraSpaceAfter: 5 });
});

fs.writeFileSync("tables_spec.json", JSON.stringify(TABLE_SPECS, null, 1));
pres.writeFile({ fileName: "TD_prioritisation_presentation_f2.pptx" }).then(() => {
  // the speaker notes double as the spoken script
  const words = notes.reduce((a, [, , t]) => a + t.split(/\s+/).length, 0);
  let md = `# Presentation script (spoken, about ${Math.round(words / 140)} minutes)\n\nGenerated from the speaker notes of the deck. About ${words} words at 140 words per minute. Slides 20 and 21 (references) are not spoken.\n\n`;
  notes.forEach(([i, t, s]) => { md += `## Slide ${i}: ${t} (${Math.round(s.split(/\s+/).length / 140 * 60)} s)\n\n${s.split("\n").join("\n\n")}\n\n`; });
  fs.writeFileSync("presentation_script_f2_auto.md", md);
  console.log("slides", n, "words", words);
});
