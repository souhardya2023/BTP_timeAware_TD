#!/bin/bash
# Regenerates the figures and score files from the data inside project/ and refreshes figures/.
#   PYP  python with matplotlib (plots)               default: python3
#   PYS  python with pandas, scikit-learn, statsmodels, scipy (analysis)   default: python3 (see requirements.txt)
#   FULL=1 also runs the slow analyses (rule discovery s2_rules.py, ~10 min)
# Needs NO git clones of the studied repositories. Steps that need them (mining, code text, clone detection) are listed in README.md and are not run here.
# Run from anywhere:  bash reproduce/regenerate.sh   (it works in place on the folders of this repository and rewrites their figures / result files with identical content)
PYP=${PYP:-python3}
PYS=${PYS:-python3}
FR="$(cd "$(dirname "$0")" && pwd)"; P="$(dirname "$FR")"; ok=0; bad=0
run() { # run DIR PYTHON SCRIPT
  ( cd "$P/$1" && timeout 900 "$2" "$3" > "$FR/logs/$(echo "$1/$3" | tr '/' '_').log" 2>&1 ) && { echo "OK   $1/$3"; ok=$((ok+1)); } || { echo "FAIL $1/$3 (see logs/)"; bad=$((bad+1)); }
}
mkdir -p "$FR/logs"
run presentation $PYS prioritization_eval.py
run presentation $PYS capture_curve.py
run presentation $PYP make_figures.py
run presentation $PYP make_architecture.py
run presentation $PYP make_tables.py
for s in diagrams.py diagrams2.py real_results.py synthetic_figures.py experiment_figures.py combined_figures.py; do run presentation/new_figures $PYP $s; done
run new_presentation/previous_talk_graphs/code $PYP r3_make_graphs.py
run insights/code $PYP make_insight_figures.py
run insights/synthetic/code $PYP s_figures.py
run insights/synthetic/code $PYP s_fig_protocols.py
run real_project_analysis/code $PYP a5_figures.py
run synthetic_dataset_v2 $PYP make_figures.py
run scenario_analysis/code $PYS s1_scenarios.py
[ -n "$FULL" ] && run scenario_analysis/code $PYS s2_rules.py
run scenario_analysis/code $PYP s3_figures.py
run scenario_analysis/code $PYP s4_scenario_plots.py
run code_insights/code $PYS c2_traits.py
run code_insights/code $PYS c4_rates.py
run code_insights/code $PYS k2_clone_tests.py
run presentation/insight_slides $PYP make_figs.py
"$PYP" "$FR/tools/collect_figures.py"
"$PYS" "$FR/tools/collect_scores.py"
echo "steps ok: $ok, failed: $bad"
