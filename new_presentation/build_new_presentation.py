"""Builds new_presentation/ from the outputs of the analyses: only what is NEW relative to the current talk (presentation/TD-presentation.pptx).
Not included (already in the talk): the real data set steps and facts (R12), the time-feature results and controls (R8), the ranking by the learned model and its capture
curve (R5), and the figures that show them.   python build_new_presentation.py   (run from anywhere)"""
import os, re, shutil, glob
HERE = os.path.dirname(os.path.abspath(__file__)); FF = os.path.abspath(os.path.join(HERE, ".."))
NF = os.path.join(FF, "presentation", "new_figures")
OLD_IDS = ["R5", "R8", "R12"]                      # insights already in the talk
FIG = os.path.join(HERE, "figures")
if os.path.exists(FIG): shutil.rmtree(FIG)
LAYOUT = {   # new folder -> list of (source folder in new_figures, file pattern)
    "01_new_dataset": [("01_dataset_creation", "synthetic_dataset_creation.png"), ("01_dataset_creation", "code_to_image_examples.png"), ("01_dataset_creation", "history_as_time_series.png"), ("03_synthetic_dataset", "S*.png")],
    "02_real_data_insights": [("04_insights", "real_i[1-5]_*.png"), ("04_insights", "real_i[7-9]_*.png"), ("04_insights", "real_i10_*.png"), ("02_real_results", "R5_size_vs_persistence.png")],
    "03_synthetic_analysis": [("04_insights", "synthetic_sf*.png")],
    "04_new_experiments": [("05_new_experiments", "E*.png")],
    "05_combined": [("06_combined", "C*.png")],
}
newdir = {}                                         # (old folder code, file) -> new folder
code = {"01_dataset_creation": "01", "02_real_results": "02", "03_synthetic_dataset": "03", "04_insights": "04", "05_new_experiments": "05", "06_combined": "06"}
for nd, items in LAYOUT.items():
    os.makedirs(os.path.join(FIG, nd), exist_ok=True)
    for sf, pat in items:
        for f in sorted(glob.glob(os.path.join(NF, sf, pat))):
            shutil.copy(f, os.path.join(FIG, nd, os.path.basename(f))); newdir[(code[sf], os.path.basename(f))] = nd
# ---- the insights text without the insights that are already in the talk
t = open(os.path.join(FF, "INSIGHTS_ALL.txt")).read().split("\n")
out, skip = [], False
start = re.compile(r"^([A-Z]\d+)\s")
for line in t:
    m = start.match(line)
    if m and m.group(1) in OLD_IDS: skip = True; continue
    if skip and (start.match(line) or line.startswith("====") or line.startswith("PART ")): skip = False
    if not skip: out.append(line)
s = "\n".join(out)
# index lines of figures that are not copied
keep = []
for line in s.split("\n"):
    m = re.match(r"^\s+([\w]+\.png)\s*\.*\s", line)
    if m and line.strip().endswith(tuple("0123456789")) is False: pass
    keep.append(line)
s = "\n".join(keep)
# figure references NN/file.png -> new folder
def sub_fig(m):
    k = (m.group(1), m.group(2))
    return (newdir[k] + "/" + m.group(2)) if k in newdir else m.group(0)
s = re.sub(r"\b(0[1-6])/([\w]+\.png)", sub_fig, s)
s = s.replace("(paths start from final_folder/presentation/new_figures/)", "(paths start from final_folder/new_presentation/figures/)")
a = s.index("Short names for the figure folders:"); b = s.index("The two datasets")
s = s[:a] + """Figure folders (final_folder/new_presentation/figures/):
    01_new_dataset  02_real_data_insights  03_synthetic_analysis  04_new_experiments  05_combined

""" + s[b:]
s = s.replace("INSIGHTS OF THE WHOLE PROJECT: REAL DATA, SYNTHETIC DATA, AND BOTH TOGETHER", "NEW INSIGHTS ONLY: REAL DATA, SYNTHETIC DATA, AND BOTH TOGETHER")
s = s.replace("====================================================================================================\n0. THE TEN THINGS TO REMEMBER", """NOTE. This file lists only the insights that are NOT already in the current talk (TD-presentation.pptx).
Left out because they are in the talk: R5 (the learned ranking ties persistence, amounts cannot be predicted),
R8 (the time feature gain and its controls) and R12 (the real data set steps and facts). The numbering is
that of the full file final_folder/INSIGHTS_ALL.txt, so the gaps are intended. Corrections to statements in
the talk are in Part F.

====================================================================================================
0. THE TEN THINGS TO REMEMBER""", 1)
s = s.replace("8. \"The classifier does not generalise to new projects\" was one project (boltons) and depends on\n    the model; the time-feature gain depends on the time model.                         [R7, R8]", "8. \"The classifier does not generalise to new projects\" was one project (boltons) and depends on\n    the model.                                                                              [R7]")
s = s.replace(" 4. The ranking is stuck at what size and history already say; the release clock is calibration,\n    not timing.                                                                   [A5, A6, R6, R9]", " 4. The ranking is stuck at what size and history already say; the release clock is calibration,\n    not timing.                                                                   [A5, A6, R6, R9]")
s = s.replace("CAN BE CLAIMED (real evidence): A1-A3, A5-A9, R1, R2, R5-R8, R10, R12.", "CAN BE CLAIMED (real evidence): A1-A3, A5-A9, R1, R2, R6, R7, R10.")
s = s.replace("Negative results to report honestly: J10, the code-image and history-image CNNs, the time-feature\n                conditionality (R8).", "Negative results to report honestly: J10, the code-image and history-image CNNs, frozen CodeBERT.")
# the index (Part G): drop lines of figures that were not copied
lines = s.split("\n"); res = []
idx = False
for ln in lines:
    if ln.startswith("PART G."): idx = True
    if ln.startswith("PART H."): idx = False
    if idx:
        m = re.match(r"^    ([\w]+\.png) \.+ ", ln)
        if m and not any(m.group(1) == k[1] for k in newdir): continue
        # folder headings of the index: rename
        for old, new in (("01_dataset_creation", "01_new_dataset"), ("02_real_results", "02_real_data_insights"), ("03_synthetic_dataset", "01_new_dataset (S-figures)"), ("04_insights", "02_real_data_insights / 03_synthetic_analysis"), ("05_new_experiments", "04_new_experiments"), ("06_combined", "05_combined")):
            if ln.strip() == old: ln = old + "   ->   " + new
    res.append(ln)
s = "\n".join(res)
s = s.replace("R8 the time gain depends on the time model (true by how time was built);\n    R12 dataset facts; every Part C item", "every Part C item")
open(os.path.join(HERE, "INSIGHTS_NEW_ONLY.txt"), "w").write(s)
# ---- reports and data
for d in ("reports", "data"):
    if os.path.exists(os.path.join(HERE, d)): shutil.rmtree(os.path.join(HERE, d))
    os.makedirs(os.path.join(HERE, d))
for src, name in (("insights/INSIGHTS.md", "INSIGHTS_real_histories.md"), ("insights/synthetic/INSIGHTS_SYNTHETIC.md", "INSIGHTS_synthetic_analysis.md"), ("insights/new/INSIGHTS_NEW.md", "INSIGHTS_new_experiments.md"),
                  ("synthetic_dataset/README.md", "synthetic_dataset_README.md"), ("synthetic_dataset/VALIDATION.md", "synthetic_dataset_VALIDATION.md"), ("synthetic_dataset/insight_check.md", "synthetic_dataset_insight_check.md")):
    shutil.copy(os.path.join(FF, src), os.path.join(HERE, "reports", name))
for sub in ("insights/results", "insights/synthetic/results", "insights/new/results", "synthetic_dataset"):
    d = os.path.join(HERE, "data", sub.replace("/", "_")); os.makedirs(d, exist_ok=True)
    for f in glob.glob(os.path.join(FF, sub, "*")):
        if os.path.isfile(f) and os.path.splitext(f)[1] in (".txt", ".csv") and os.path.getsize(f) < 250000: shutil.copy(f, d)
shutil.copy(os.path.join(FF, "INSIGHTS_ALL.txt"), os.path.join(HERE, "reports", "INSIGHTS_ALL_full.txt"))
n = sum(len(fs) for _, _, fs in os.walk(FIG))
print("figures", n, "| insights lines", len(s.split("\n")))
