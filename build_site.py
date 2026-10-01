"""Assert published findings against exact outputs, check original API controls,
and synchronize local explorer assets. No network or source refresh occurs.
"""
from collections import Counter
import csv
import io
import json
from pathlib import Path
import re
import shutil
import struct
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parent


def main():
    model = json.loads((ROOT / "results/analysis.json").read_text())
    manifest = json.loads((ROOT / "source/manifest.json").read_text())
    controls = json.loads((ROOT / "source/remote-controls.json").read_text())
    with ZipFile(ROOT / "source/nyc311-2024-01.csv.zip") as z:
        rows = list(csv.DictReader(io.StringIO(z.read(manifest["raw_member"]).decode("utf-8-sig"))))
    assert len(rows) == int(controls["cohort_count"]["records"][0]["requests"]) == 287186
    grouped = Counter((r["agency"], r["borough"], r["status"]) for r in rows)
    remote = {(r["agency"], r["borough"], r["status"]): int(r["requests"]) for r in controls["agency_borough_status"]["records"]}
    assert grouped == remote
    daily = Counter(r["created_date"][:10] for r in rows)
    remote_days = {next(v[:10] for k, v in r.items() if k != "requests"): int(r["requests"]) for r in controls["daily"]["records"]}
    assert daily == remote_days
    m = model["views"]["all|all"]["metrics"]
    q = model["quality"]
    assert m["requests"] == 287186 and m["closed_status"] == 285297 and m["timing_eligible"] == 284017
    assert m["not_closed_status"] == 1889 and m["closed_excluded_from_timing"] == 1280
    assert f'{m["median_hours"]:.2f}' == "19.10" and f'{m["mean_hours"]:.2f}' == "317.63" and f'{m["p90_hours"]:.2f}' == "668.55"
    assert m["within_24h"] == 152789 and f'{m["within_24h_share_of_eligible"]*100:.2f}' == "53.80"
    assert m["upper_iqr_outliers"] == 49374 and m["zero_duration"] == 3809 and m["negative_duration"] == 75
    assert m["nonclosed_with_close_date"] == 208
    assert q["closed_status_missing_close_date"] == 1280 and q["future_close_requests"] == 0
    assert q["exact_duplicate_rows_removed"] == q["conflicting_id_rows"] == q["quarantined_rows"] == 0
    assert q["missing_zip_requests"] == 3090 and q["invalid_nonmissing_zip_requests"] == 0
    assert q["unknown_borough_requests"] == 193 and q["unexpected_borough_requests"] == 0
    assert q["raw_blank_count"]["descriptor"] == 1706 and q["normalized_missing_count"]["descriptor"] == 7466
    assert q["raw_blank_count"]["location_type"] == 33625 and q["normalized_missing_count"]["location_type"] == 33632
    assert q["normalized_missing_count"]["due_date"] == 285757 and f'{285757/m["requests"]*100:.2f}' == "99.50"
    assert q["whitespace_changed_cells"]["descriptor"] == 24
    assert q["outlier_rule"]["upper_fence_seconds"] == 769379.5 and f'{769379.5/86400:.2f}' == "8.90"
    top = model["views"]["all|all"]["problems"][:3]
    assert [(r["name"], r["requests"]) for r in top] == [("HEAT/HOT WATER", 51325), ("Illegal Parking", 41124), ("Noise - Residential", 22091)]
    assert sum(r["requests"] for r in top) == 114540 and f'{114540/m["requests"]*100:.2f}' == "39.88"
    sensitivity = model["sensitivity"]
    for key, n, median, mean in [("all_eligible",284017,"19.10","317.63"),
                                ("excluding_upper_iqr_outliers_diagnostic_only",234643,"6.71","28.09"),
                                ("excluding_zero_duration_diagnostic_only",280208,"20.04","321.95")]:
        s = sensitivity[key]
        assert s["timing_eligible"] == n and f'{s["median_hours"]:.2f}' == median and f'{s["mean_hours"]:.2f}' == mean
    comparison = {r["name"]:r for r in model["same_problem_comparisons"]["HEAT/HOT WATER"]}
    expected = {"Bronx":(18483,18477,"29.59"),"Brooklyn":(13233,13205,"39.97"),"Manhattan":(11196,11178,"45.48"),"Queens":(7859,7845,"36.43"),"Staten Island":(554,554,"41.22")}
    for borough,(n,t,median) in expected.items():
        r=comparison[borough];assert (r["requests"],r["timing_eligible"],f'{r["median_hours"]:.2f}') == (n,t,median)
    assert min(r["median_hours"] for r in comparison.values() if r["median_hours"] is not None) == comparison["Bronx"]["median_hours"]
    assert max(r["median_hours"] for r in comparison.values() if r["median_hours"] is not None) == comparison["Manhattan"]["median_hours"]
    longest = model["outlier_examples"][0]
    assert str(longest["request_id"]) == "59916703"
    assert f'{longest["closure_days"]:.2f}' == "984.93"
    assert len(model["agencies"]) == 14 and len(model["boroughs"]) == 6 and len(model["views"]) == 105
    selected = {k:model[k] for k in ("cohort","snapshot_utc","source_url","source_raw_sha256","agencies","boroughs","views","quality","sensitivity","same_problem_comparisons")}
    site = ROOT / "site";site.mkdir(exist_ok=True)
    (site/"data.js").write_text("window.NYC311_DATA = " + json.dumps(selected, ensure_ascii=False, separators=(",",":"), allow_nan=False) + ";\n",encoding="utf-8")
    shutil.copytree(ROOT/"figures",site/"figures",dirs_exist_ok=True)
    for name in ("CASE_STUDY.md","INTERVIEW_BRIEF.md","VERIFICATION.md","CLEANING_DECISIONS.md"):
        if (ROOT/name).exists():shutil.copy2(ROOT/name,site/name)
    html=(site/"index.html").read_text()
    for name in ("problem-volume","closure-distribution","missingness","daily-intake","same-problem-boroughs"):
        width,height=struct.unpack(">II",(ROOT/"figures"/(name+".png")).read_bytes()[16:24])
        html=re.sub(r'(src="figures/'+name+r'\.png"[^>]*?width=")\d+(" height=")\d+("[^>]*>)',lambda m:m[1]+str(width)+m[2]+str(height)+m[3],html)
    (site/"index.html").write_text(html)
    result={"status":"passed","official_count_checked":len(rows),"official_agency_borough_status_cells_checked":len(grouped),"official_daily_counts_checked":len(daily),"published_narrative_metrics_asserted":True,"all_raw_negative_intervals_are_nonclosed":all(r["status"].upper()!="CLOSED" for r in rows if r["closed_date"] and r["closed_date"]<r["created_date"]),"source_url":manifest["landing_url"]}
    assert result["all_raw_negative_intervals_are_nonclosed"]
    (ROOT/"results/publication-checks.json").write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result))


if __name__ == "__main__":main()
