"""Independent reference calculations using csv/datetime/collections, not Pandas.

Checks every published filter view, category/daily/hourly count and timing metric
against raw records. Uses no cleaning or aggregation functions from analysis.py.
"""
from collections import Counter, defaultdict
import csv
from datetime import datetime, timezone
import hashlib
import io
import json
import math
from pathlib import Path
import re
from statistics import fmean
import sys
from zipfile import ZipFile
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent
ZONE = ZoneInfo("America/New_York")


def text(value):
    value = re.sub(r"\s+", " ", value.strip())
    return None if value.upper() in {"", "NA", "N/A", "NULL", "<NA>"} else value


def parse_local(value):
    if value is None:
        return None
    try:
        result = datetime.fromisoformat(value)
        return result if result.tzinfo is None else None
    except ValueError:
        return None


def utc(value):
    if value is None:
        return None
    candidates = [value.replace(tzinfo=ZONE, fold=i) for i in (0, 1)]
    valid = [c for c in candidates if c.astimezone(timezone.utc).astimezone(ZONE).replace(tzinfo=None) == value]
    if not valid or (len(valid) == 2 and valid[0].utcoffset() != valid[1].utcoffset()):
        return None
    return valid[0].astimezone(timezone.utc)


def quantile(values, q):
    if not values:
        return None
    values = sorted(values)
    position = (len(values) - 1) * q
    lo = int(math.floor(position))
    hi = int(math.ceil(position))
    return values[lo] + (values[hi] - values[lo]) * (position - lo)


def near(actual, expected, name):
    if actual is None or expected is None:
        assert actual == expected, (name, actual, expected)
    elif isinstance(expected, float):
        assert math.isclose(actual, expected, rel_tol=1e-11, abs_tol=1e-8), (name, actual, expected)
    else:
        assert actual == expected, (name, actual, expected)


def expected_metrics(records, fence):
    durations = [r["seconds"] for r in records if r["eligible"]]
    n, closed, eligible = len(records), sum(r["closed"] for r in records), len(durations)
    within = sum(s <= 86400 for s in durations)
    return {"requests": n, "closed_status": closed, "not_closed_status": n - closed,
            "timing_eligible": eligible, "closed_excluded_from_timing": closed - eligible,
            "closed_status_share": closed / n if n else None,
            "median_hours": quantile(durations, .5) / 3600 if eligible else None,
            "p90_hours": quantile(durations, .9) / 3600 if eligible else None,
            "mean_hours": fmean(durations) / 3600 if eligible else None,
            "within_24h": within, "within_24h_share_of_eligible": within / eligible if eligible else None,
            "zero_duration": sum(s == 0 for s in durations),
            "upper_iqr_outliers": sum(s > fence for s in durations),
            "unknown_zip": sum(r["zip"] is None for r in records),
            "invalid_nonmissing_zip": sum(r["zip"] is not None and re.fullmatch(r"\d{5}", r["zip"]) is None for r in records),
            "negative_duration": sum(r["negative"] for r in records),
            "nonclosed_with_close_date": sum(not r["closed"] and r["closed_local"] is not None for r in records)}


def reference_rows(root=ROOT):
    m = json.loads((root / "source/manifest.json").read_text())
    with ZipFile(root / "source/nyc311-2024-01.csv.zip") as z:
        data = z.read(m["raw_member"])
    assert hashlib.sha256(data).hexdigest() == m["raw_sha256"]
    raw = list(csv.DictReader(io.StringIO(data.decode("utf-8-sig"))))
    keys = m["fields"]
    seen, unique = set(), []
    for row in raw:
        signature = tuple(row[c] for c in keys)
        if signature not in seen:
            seen.add(signature)
            unique.append({c: text(row[c]) for c in keys})
    id_counts = Counter(r["unique_key"] for r in unique if r["unique_key"] is not None)
    cutoff = datetime.fromisoformat(m["retrieval_started_utc"])
    start, end = datetime.fromisoformat(m["cohort_start"]), datetime.fromisoformat(m["cohort_end_exclusive"])
    accepted = []
    for r in unique:
        created, closed = parse_local(r["created_date"]), parse_local(r["closed_date"])
        if r["unique_key"] is None or not re.fullmatch(r"\d+", r["unique_key"]) or id_counts[r["unique_key"]] > 1 or created is None or not start <= created < end:
            continue
        cu, cl = utc(created), utc(closed)
        seconds = (cl - cu).total_seconds() if cu and cl else None
        is_closed = (r["status"] or "Unknown").upper() == "CLOSED"
        negative = seconds is not None and seconds < 0
        boro = (r["borough"] or "UNSPECIFIED").upper()
        accepted.append({"id": r["unique_key"], "agency": (r["agency"] or "Unknown").upper(),
                         "borough": "Unknown / unassigned" if boro == "UNSPECIFIED" else boro.title(),
                         "problem": r["complaint_type"] or "Unknown", "channel": (r["open_data_channel_type"] or "Unknown").upper(),
                         "status": (r["status"] or "Unknown").upper(), "closed": is_closed,
                         "closed_local": closed, "day": created.strftime("%Y-%m-%d"), "hour": created.hour,
                         "seconds": seconds, "eligible": bool(is_closed and seconds is not None and not negative and cl <= cutoff),
                         "negative": negative, "zip": r["incident_zip"]})
    return raw, unique, accepted


def validate(root=ROOT, output=None):
    output = output or root / "results"
    published = json.loads((output / "analysis.json").read_text())
    raw, unique, rows = reference_rows(root)
    durations = [r["seconds"] for r in rows if r["eligible"]]
    q1, q3 = quantile(durations, .25), quantile(durations, .75)
    fence = q3 + 1.5 * (q3 - q1)
    near(published["quality"]["outlier_rule"]["q1_seconds"], q1, "q1")
    near(published["quality"]["outlier_rule"]["q3_seconds"], q3, "q3")
    near(published["quality"]["outlier_rule"]["upper_fence_seconds"], fence, "fence")
    groups = defaultdict(list)
    for r in rows:
        for a, b in [("all", "all"), (r["agency"], "all"), ("all", r["borough"]), (r["agency"], r["borough"])]:
            groups[a + "|" + b].append(r)
    metric_checks, count_checks = 0, 0
    for key, view in published["views"].items():
        selected = groups[key]
        expected = expected_metrics(selected, fence)
        for metric, value in expected.items():
            near(view["metrics"][metric], value, key + ":" + metric)
            metric_checks += 1
        daily, hourly = Counter(r["day"] for r in selected), Counter(r["hour"] for r in selected)
        for row in view["daily"]:
            near(row["requests"], daily[row["day"]], key + ":day")
            count_checks += 1
        for row in view["hourly"]:
            near(row["requests"], hourly[row["hour"]], key + ":hour")
            count_checks += 1
        for dimension in ["problem", "channel", "status"]:
            expected_counts = Counter(r[dimension] for r in selected)
            plural = {"problem": "problems", "channel": "channels", "status": "statuses"}[dimension]
            assert {r["name"]: r["requests"] for r in view[plural]} == dict(expected_counts), (key, dimension)
            if dimension != "status":
                for category in view[plural]:
                    subset = [r for r in selected if r[dimension] == category["name"]]
                    for metric, value in expected_metrics(subset, fence).items():
                        near(category[metric], value, key + ":" + dimension + ":" + metric)
                        metric_checks += 1
            count_checks += len(expected_counts)
        bins = Counter()
        for r in selected:
            if r["eligible"]:
                s = r["seconds"]
                index = 0 if s <= 3600 else 1 if s <= 86400 else 2 if s <= 604800 else 3 if s <= 2592000 else 4 if s <= 7776000 else 5
                bins[index] += 1
        assert [r["requests"] for r in view["duration_bins"]] == [bins[i] for i in range(6)], key
        assert sum(daily.values()) == expected["requests"]
        assert sum(bins.values()) == expected["timing_eligible"]
    for name, dimension in [("agency_summary", "agency"), ("borough_summary", "borough")]:
        for row in published[name]:
            selected = [r for r in rows if r[dimension] == row["name"]]
            for metric, value in expected_metrics(selected, fence).items():
                near(row[metric], value, name + ":" + metric)
                metric_checks += 1
    for problem, comparisons in published["same_problem_comparisons"].items():
        for row in comparisons:
            selected = [r for r in rows if r["problem"] == problem and r["borough"] == row["name"]]
            for metric, value in expected_metrics(selected, fence).items():
                near(row[metric], value, "same_problem:" + metric)
                metric_checks += 1
    for name, selected in [("all_eligible", rows), ("excluding_upper_iqr_outliers_diagnostic_only", [r for r in rows if not (r["eligible"] and r["seconds"] > fence)]), ("excluding_zero_duration_diagnostic_only", [r for r in rows if not (r["eligible"] and r["seconds"] == 0)])]:
        for metric, value in expected_metrics(selected, fence).items():
            near(published["sensitivity"][name][metric], value, "sensitivity:" + metric)
            metric_checks += 1
    examples = sorted([r for r in rows if r["eligible"]], key=lambda r: (-r["seconds"], r["id"]))[:12]
    for actual, expected in zip(published["outlier_examples"], examples):
        assert actual["request_id"] == expected["id"]
        near(actual["closure_days"], expected["seconds"] / 86400, "outlier_example")
    quality = published["quality"]
    assert quality["raw_rows"] == len(raw)
    assert quality["exact_duplicate_rows_removed"] == len(raw) - len(unique)
    assert quality["accepted_requests"] == len(rows)
    assert quality["quarantined_rows"] == len(unique) - len(rows)
    for c in raw[0]:
        assert quality["raw_blank_count"][c] == sum(r[c] == "" for r in raw), c
        assert quality["normalized_missing_count"][c] == sum(r[c] is None for r in unique), c
    unique_signatures = set()
    whitespace = Counter()
    for r in raw:
        signature = tuple(r.values())
        if signature in unique_signatures:
            continue
        unique_signatures.add(signature)
        for c, value in r.items():
            whitespace[c] += value != re.sub(r"\s+", " ", value.strip())
    assert quality["whitespace_changed_cells"] == {c: whitespace[c] for c in raw[0]}
    for c in ["created_date", "closed_date", "due_date", "resolution_action_updated_date"]:
        parsed = [parse_local(r[c]) for r in unique]
        assert quality["date_parse_failures"][c] == sum(r[c] is not None and d is None for r, d in zip(unique, parsed))
        assert quality["timezone_unresolvable_count"][c] == sum(d is not None and utc(d) is None for d in parsed)
    id_counts = Counter(r["unique_key"] for r in unique if r["unique_key"] is not None)
    assert quality["invalid_id_rows"] == sum(r["unique_key"] is None or re.fullmatch(r"\d+", r["unique_key"]) is None for r in unique)
    assert quality["conflicting_id_rows"] == sum(r["unique_key"] is not None and id_counts[r["unique_key"]] > 1 for r in unique)
    assert quality["conflicting_unique_ids"] == sum(count > 1 for count in id_counts.values())
    assert quality["invalid_created_rows"] == sum(parse_local(r["created_date"]) is None for r in unique)
    start, end = datetime(2024, 1, 1), datetime(2024, 2, 1)
    assert quality["out_of_cohort_rows"] == sum(parse_local(r["created_date"]) is not None and not start <= parse_local(r["created_date"]) < end for r in unique)
    assert quality["unknown_borough_requests"] == sum(r["borough"] == "Unknown / unassigned" for r in rows)
    expected_boroughs = {"Bronx", "Brooklyn", "Manhattan", "Queens", "Staten Island", "Unknown / unassigned"}
    assert quality["unexpected_borough_requests"] == sum(r["borough"] not in expected_boroughs for r in rows)
    assert quality["missing_zip_requests"] == sum(r["zip"] is None for r in rows)
    assert quality["invalid_nonmissing_zip_requests"] == sum(r["zip"] is not None and re.fullmatch(r"\d{5}", r["zip"]) is None for r in rows)
    assert quality["negative_duration_requests"] == sum(r["negative"] for r in rows)
    assert quality["closed_status_missing_close_date"] == sum(r["closed"] and r["closed_local"] is None for r in rows)
    assert quality["nonclosed_status_with_close_date"] == sum(not r["closed"] and r["closed_local"] is not None for r in rows)
    cutoff = datetime.fromisoformat(json.loads((root / "source/manifest.json").read_text())["retrieval_started_utc"])
    assert quality["future_close_requests"] == sum(utc(r["closed_local"]) is not None and utc(r["closed_local"]) > cutoff for r in rows)
    assert quality["closure_time_eligible_requests"] == len(durations)
    checks = {"status": "passed", "reference": "raw CSV with independent stdlib csv/datetime/zoneinfo/collections/statistics code; no Pandas cleaning functions",
              "raw_rows_checked": len(raw), "accepted_requests_checked": len(rows), "filter_views_checked": len(published["views"]),
              "scalar_metric_comparisons": metric_checks, "distribution_count_comparisons": count_checks,
              "outlier_examples_checked": len(examples), "all_published_agency_borough_problem_channel_metrics_checked": True,
              "same_problem_comparisons_checked": len(published["same_problem_comparisons"]), "sensitivity_views_checked": 3,
              "source_missingness_whitespace_duplicate_date_and_eligibility_audits_checked": True}
    (output / "validation.json").write_text(json.dumps(checks, indent=2) + "\n")
    print(json.dumps(checks))
    return checks


if __name__ == "__main__":
    validate(output=Path(sys.argv[1]) if len(sys.argv) > 1 else None)
