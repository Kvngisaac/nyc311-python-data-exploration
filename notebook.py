"""Build and execute a teaching notebook with a transparent CPython cell runner.

No Jupyter kernel is used or claimed. Cells are normal Python, executed in a
shared namespace; stdout and explicit rich displays are captured into nbformat4.
The generated notebook can also be opened and run with a Python Jupyter kernel.
"""
import base64
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import traceback

ROOT = Path(__file__).resolve().parent


def main():
    cells=[]
    def md(text):cells.append({"cell_type":"markdown","metadata":{},"source":text.splitlines(keepends=True)})
    def code(text):cells.append({"cell_type":"code","execution_count":None,"metadata":{},"outputs":[],"source":text.splitlines(keepends=True)})
    md("# NYC311: trustworthy Python exploration\n\nAI-assisted portfolio case study. The included runner executes these Python cells using CPython, not a Jupyter kernel. Outputs below come from the pinned source; synthetic boundary fixtures are not mixed with findings.\n\n**Question:** where does January 2024 intake concentrate, and which data-quality issues affect recorded closure reporting?\n\nThe source is an October 2026 snapshot of requests *created* in January 2024. Closed is administrative status, not proof of a fix.")
    code("from pathlib import Path\nimport sys, json\nimport pandas as pd\nif 'display_png' not in globals():\n    from IPython.display import display, Image\n    def display_png(path): display(Image(filename=str(path)))\n# Supports running from the repository root or notebooks/ in Jupyter.\nROOT = Path.cwd()\nif not (ROOT / 'analysis.py').exists(): ROOT = ROOT.parent\nsys.path.insert(0, str(ROOT))\nfrom analysis import read_snapshot, clean_data, metrics, group_metrics\nraw, manifest = read_snapshot(ROOT)\nprint('Rows:', len(raw), 'Columns:', len(raw.columns))\nprint('Retrieved:', manifest['retrieval_started_utc'])\nprint('Raw SHA-256:', manifest['raw_sha256'])\nprint(raw.dtypes.to_string())\nprint(raw.head(3).to_string(index=False))")
    md("## Inspect first: blanks and duplicate keys\nDo not assume blank is the only missing representation. Exact duplicates and repeated request IDs are separate questions; counts below describe the actual snapshot.")
    code("inspection = pd.DataFrame({'raw_blanks': raw.eq('').sum(), 'distinct_raw_values': raw.nunique()})\nprint(inspection.to_string())\nprint('Exact repeats:', int(raw.duplicated().sum()))\nprint('Rows with repeated nonblank IDs:', int((raw.unique_key.ne('') & raw.unique_key.duplicated(keep=False)).sum()))")
    md("## Clean with explicit gates\nIDs/ZIPs stay strings. Normalize whitespace/null tokens, parse dates, localize New York time, and separate accepted volume from eligible closure timing. No missing dates are filled and no valid outliers are deleted.")
    code("clean, quality, quarantine = clean_data(raw, manifest)\nprint('Accepted:', len(clean), 'Quarantined:', len(quarantine))\nmissing = pd.DataFrame({'raw_blanks': quality['raw_blank_count'], 'normalized_missing': quality['normalized_missing_count']})\nmissing['normalized_share'] = missing.normalized_missing / len(raw)\nprint(missing.to_string())\nfor key in ['closed_status_missing_close_date','nonclosed_status_with_close_date','negative_duration_requests','future_close_requests','unknown_borough_requests']:\n    print(key, quality[key])\nprint('Parse failures:', quality['date_parse_failures'])\nprint('DST-unresolved:', quality['timezone_unresolvable_count'])")
    md("## Check the measurement population\nEvery accepted request belongs to volume analysis. Timing requires Closed status and a valid nonnegative UTC-adjusted interval, with no future closure. The 75 negative intervals are all non-Closed; they are not an extra subtraction from the Closed count.")
    code("overall = metrics(clean)\nprint(json.dumps(overall, indent=2))\nassert overall['requests'] == 287186\nassert overall['closed_status'] == 285297\nassert overall['timing_eligible'] == 284017\nassert clean.loc[clean.negative_duration, 'is_closed'].sum() == 0\nprint(pd.crosstab(clean.status_clean, clean.closed_date_local.isna(), dropna=False).to_string())")
    md("## Group and aggregate: demand concentration\nUse all accepted requests for demand share and a separate timing denominator inside each group. A request is not a unique person or incident.")
    code("problems = pd.DataFrame(group_metrics(clean, 'problem_clean'))\nproblems['request_share'] = problems.requests / len(clean)\nprint(problems[['name','requests','request_share','timing_eligible','median_hours','p90_hours']].head(10).to_string(index=False))\ntop3 = int(problems.head(3).requests.sum())\nprint('Top 3 requests:', top3, 'Share:', f'{top3 / len(clean):.2%}')\nassert top3 == 114540\nprint('Local weekday intake:')\nprint(clean.groupby('created_weekday', observed=True).size().to_string())\nassert clean.groupby('created_weekday', observed=True).size().sum() == len(clean)")
    md("## Investigate outliers instead of deleting them\nThe global IQR fence is a review flag. Trace the source dates, and explain how removing valid long or zero durations changes the population and its estimate.")
    code("timed = clean.loc[clean.timing_eligible, 'closure_seconds']\nprint('IQR rule:', quality['outlier_rule'])\nprint('Long flags:', int(clean.upper_iqr_outlier.sum()), 'Zero durations:', int(timed.eq(0).sum()))\nlongest = clean.loc[clean.timing_eligible].nlargest(5, 'closure_seconds')\nprint(longest[['unique_key','agency_clean','problem_clean','created_date','closed_date','closure_seconds']].to_string(index=False))\nfor label, frame in [('default',clean),('exclude upper fence: diagnostic only',clean.loc[~clean.upper_iqr_outlier]),('exclude zero: diagnostic only',clean.loc[~(clean.timing_eligible & clean.closure_seconds.eq(0))])]:\n    m = metrics(frame)\n    print(label, 'timed n',m['timing_eligible'],'median h',round(m['median_hours'],2),'mean h',round(m['mean_hours'],2))")
    md("## Compare one problem across locations\nSame-category comparisons reduce one mix difference. They do not control severity, repeat incidents, reporting behavior, or administrative workflow. No causal location ranking is justified.")
    code("heat = clean.loc[clean.problem_clean.eq('HEAT/HOT WATER')]\ncomparison = pd.DataFrame(group_metrics(heat, 'borough_clean'))\nprint(comparison[['name','requests','timing_eligible','median_hours','p90_hours']].to_string(index=False))")
    md("## Visual evidence\nThese five figures are regenerated by `visualize.py` from the exact validated model. Each has a standalone SVG version and explicit scope/denominator.")
    for name in ("problem-volume","daily-intake","closure-distribution","missingness","same-problem-boroughs"):
        code(f"display_png(ROOT / 'figures/{name}.png')")
    md("## Validation and limitations\nIndependent stdlib raw-CSV calculations match all published metrics, distributions, quality audits, 105 filter views, sensitivity views, same-problem comparisons, and outlier traces. Synthetic tests cover absent boundary cases. Source-side totals/groups/days provide a separate extraction control.\n\nOne winter month is not annual seasonality. Records are mutable, demand is not population-adjusted, Closed is not proof of repair, and non-Closed/missing-date records are censored from timing estimates. No universal SLA, service outcome, or causal ranking is established. Browser QA and actual Jupyter-kernel execution remain distinct from this CPython cell execution.")
    code("evidence = json.loads((ROOT / 'results/validation.json').read_text())\nprint(json.dumps(evidence, indent=2))\nassert evidence['status'] == 'passed'\nprint('End of executed exploration. See INTERVIEW_BRIEF.md for explanation and practice questions.')")
    notebook={"cells":cells,"metadata":{"kernelspec":{"display_name":"Python 3","language":"python","name":"python3"},"language_info":{"name":"python","version":sys_version()},"execution_method":"included CPython runner; no Jupyter kernel"},"nbformat":4,"nbformat_minor":5}
    environment={"__name__":"__notebook__"}
    execution=0
    import os
    previous=Path.cwd();os.chdir(ROOT)
    try:
        for index,cell in enumerate(cells):
            cell["id"]=f"nyc311-{index:02d}"
            if cell["cell_type"] != "code":continue
            execution+=1;cell["execution_count"]=execution
            def display_png(path):
                cell["outputs"].append({"output_type":"display_data","metadata":{},"data":{"image/png":base64.b64encode(Path(path).read_bytes()).decode("ascii"),"text/plain":[Path(path).name]}})
            environment["display_png"]=display_png
            output=io.StringIO()
            with redirect_stdout(output):exec(compile("".join(cell["source"]),f"notebook-cell-{execution}","exec"),environment)
            if output.getvalue():cell["outputs"].append({"name":"stdout","output_type":"stream","text":output.getvalue().splitlines(keepends=True)})
    finally:os.chdir(previous)
    folder=ROOT/"notebooks";folder.mkdir(exist_ok=True)
    (folder/"nyc311_exploration.ipynb").write_text(json.dumps(notebook,ensure_ascii=False,indent=1,allow_nan=False)+"\n",encoding="utf-8")
    receipt={"status":"passed","execution_method":"CPython shared-namespace cell runner, not Jupyter kernel","code_cells_executed":execution,"rich_figure_outputs":5,"errors":0}
    (ROOT/"results/notebook-execution.json").write_text(json.dumps(receipt,indent=2)+"\n")
    print(json.dumps(receipt))


def sys_version():
    import platform
    return platform.python_version()


if __name__ == "__main__":main()
