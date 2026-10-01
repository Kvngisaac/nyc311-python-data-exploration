"""Auditable Pandas cleaning and exploratory analysis of the pinned NYC311 cohort.

Run from any directory: python analysis.py [--output PATH]
This entry point reads the included snapshot; it never silently refreshes source data.
"""
from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
import io
import json
from pathlib import Path
from zipfile import ZipFile

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
MISSING_TOKENS = {"", "NA", "N/A", "NULL", "<NA>"}
BOROUGHS = {"BRONX", "BROOKLYN", "MANHATTAN", "QUEENS", "STATEN ISLAND"}
DATE_FIELDS = ["created_date", "closed_date", "due_date", "resolution_action_updated_date"]
BIN_LABELS = ["0–1 hour", ">1–24 hours", ">1–7 days", ">7–30 days", ">30–90 days", ">90 days"]
BIN_EDGES = [0, 3600, 86400, 604800, 2592000, 7776000, float("inf")]


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def read_snapshot(root: Path = ROOT):
    manifest = json.loads((root / "source/manifest.json").read_text())
    archive = root / "source/nyc311-2024-01.csv.zip"
    if hashlib.sha256(archive.read_bytes()).hexdigest() != manifest["snapshot_zip_sha256"]:
        raise ValueError("Snapshot ZIP checksum differs from pinned provenance")
    with ZipFile(archive) as z:
        if z.testzip() is not None or z.namelist() != [manifest["raw_member"]]:
            raise ValueError("Snapshot archive layout/integrity mismatch")
        data = z.read(manifest["raw_member"])
    if hashlib.sha256(data).hexdigest() != manifest["raw_sha256"]:
        raise ValueError("Raw CSV checksum differs from pinned provenance")
    frame = pd.read_csv(io.BytesIO(data), dtype="string", keep_default_na=False)
    if list(frame.columns) != manifest["fields"] or len(frame) != manifest["raw_rows"]:
        raise ValueError("Pinned source schema/row count mismatch")
    return frame, manifest


def clean_data(raw: pd.DataFrame, manifest: dict):
    """Keep volume records separate from the smaller closure-time denominator."""
    if list(raw.columns) != manifest["fields"]:
        raise ValueError("Unexpected source schema")
    work = raw.copy()
    audit = {"raw_rows": len(raw), "raw_dtype": {c: str(raw[c].dtype) for c in raw},
             "raw_blank_count": {c: int(raw[c].eq("").sum()) for c in raw}}
    audit["exact_duplicate_rows_removed"] = int(work.duplicated().sum())
    work = work.drop_duplicates().copy()
    changed, nulls = {}, {}
    for col in work:
        normalized = work[col].str.strip().str.replace(r"\s+", " ", regex=True)
        changed[col] = int(work[col].ne(normalized).fillna(False).sum())
        normalized = normalized.mask(normalized.str.upper().isin(MISSING_TOKENS))
        nulls[col] = int(normalized.isna().sum())
        work[col] = normalized
    audit["whitespace_changed_cells"] = changed
    audit["normalized_missing_count"] = nulls
    invalid_id = ~work["unique_key"].str.fullmatch(r"\d+").fillna(False)
    duplicate_id = work["unique_key"].notna() & work["unique_key"].duplicated(keep=False)
    audit["invalid_id_rows"] = int(invalid_id.sum())
    audit["conflicting_id_rows"] = int(duplicate_id.sum())
    audit["conflicting_unique_ids"] = int(work.loc[duplicate_id, "unique_key"].nunique())
    audit["date_parse_failures"] = {}
    audit["timezone_unresolvable_count"] = {}
    for col in DATE_FIELDS:
        parsed = pd.to_datetime(work[col], format="ISO8601", errors="coerce")
        audit["date_parse_failures"][col] = int((work[col].notna() & parsed.isna()).sum())
        # The source has local floating timestamps, not UTC offsets. Ambiguous or
        # nonexistent DST instants remain unusable, never guessed or shifted.
        utc = parsed.dt.tz_localize("America/New_York", ambiguous="NaT", nonexistent="NaT").dt.tz_convert("UTC")
        audit["timezone_unresolvable_count"][col] = int((parsed.notna() & utc.isna()).sum())
        work[col + "_local"] = parsed
        work[col + "_utc"] = utc
    invalid_created = work["created_date_local"].isna()
    out_of_cohort = (~invalid_created) & (
        work["created_date_local"].lt(pd.Timestamp(manifest["cohort_start"])) |
        work["created_date_local"].ge(pd.Timestamp(manifest["cohort_end_exclusive"])))
    audit["invalid_created_rows"] = int(invalid_created.sum())
    audit["out_of_cohort_rows"] = int(out_of_cohort.sum())
    excluded = invalid_id | duplicate_id | invalid_created | out_of_cohort
    audit["quarantined_rows"] = int(excluded.sum())
    quarantine = work.loc[excluded, ["unique_key", "created_date"]].copy()
    quarantine["invalid_id"] = invalid_id.loc[excluded]
    quarantine["conflicting_id"] = duplicate_id.loc[excluded]
    quarantine["invalid_created"] = invalid_created.loc[excluded]
    quarantine["out_of_cohort"] = out_of_cohort.loc[excluded]
    work = work.loc[~excluded].copy()
    audit["accepted_requests"] = len(work)
    work["agency_clean"] = work["agency"].str.upper().fillna("Unknown")
    work["problem_clean"] = work["complaint_type"].fillna("Unknown")
    work["channel_clean"] = work["open_data_channel_type"].str.upper().fillna("Unknown")
    borough = work["borough"].str.upper()
    work["borough_clean"] = borough.str.title().fillna("Unknown / unassigned")
    work.loc[borough.eq("UNSPECIFIED").fillna(False), "borough_clean"] = "Unknown / unassigned"
    audit["unknown_borough_requests"] = int(work["borough_clean"].eq("Unknown / unassigned").sum())
    audit["unexpected_borough_requests"] = int((borough.notna() & ~borough.isin(BOROUGHS | {"UNSPECIFIED"})).sum())
    work["status_clean"] = work["status"].str.upper().fillna("Unknown")
    work["is_closed"] = work["status_clean"].eq("CLOSED")
    # ZIP codes and request IDs stay text. ZIP formatting anomalies are flagged;
    # neither a borough nor a ZIP code is fabricated from another field.
    work["zip_valid"] = work["incident_zip"].str.fullmatch(r"\d{5}").fillna(False)
    audit["missing_zip_requests"] = int(work["incident_zip"].isna().sum())
    audit["invalid_nonmissing_zip_requests"] = int((work["incident_zip"].notna() & ~work["zip_valid"]).sum())
    work["created_day"] = work["created_date_local"].dt.strftime("%Y-%m-%d")
    work["created_hour"] = work["created_date_local"].dt.hour.astype("Int64")
    work["created_weekday"] = work["created_date_local"].dt.day_name()
    work["created_weekend"] = work["created_date_local"].dt.dayofweek.ge(5)
    work["closure_seconds"] = (work["closed_date_utc"] - work["created_date_utc"]).dt.total_seconds()
    cutoff = pd.Timestamp(manifest["retrieval_started_utc"])
    paired = work["closed_date_utc"].notna() & work["created_date_utc"].notna()
    work["negative_duration"] = paired & work["closure_seconds"].lt(0)
    work["future_close"] = work["closed_date_utc"].gt(cutoff)
    work["timing_eligible"] = work["is_closed"] & paired & ~work["negative_duration"] & ~work["future_close"]
    audit["closed_status_missing_close_date"] = int((work["is_closed"] & work["closed_date_local"].isna()).sum())
    audit["nonclosed_status_with_close_date"] = int((~work["is_closed"] & work["closed_date_local"].notna()).sum())
    audit["negative_duration_requests"] = int(work["negative_duration"].sum())
    audit["future_close_requests"] = int(work["future_close"].sum())
    eligible = work.loc[work["timing_eligible"], "closure_seconds"]
    q1, q3 = eligible.quantile([.25, .75]).tolist() if len(eligible) else [None, None]
    fence = q3 + 1.5 * (q3 - q1) if q1 is not None else None
    work["upper_iqr_outlier"] = work["timing_eligible"] & work["closure_seconds"].gt(fence if fence is not None else float("inf"))
    audit["outlier_rule"] = {"q1_seconds": q1, "q3_seconds": q3, "upper_fence_seconds": fence,
                             "method": "global eligible cohort Q3 + 1.5 × IQR; linear quantiles; investigate, do not delete"}
    audit["closure_time_eligible_requests"] = int(work["timing_eligible"].sum())
    audit["clean_dtype"] = {c: str(work[c].dtype) for c in work}
    return work, audit, quarantine


def number(value):
    return None if pd.isna(value) else float(value)


def metrics(frame: pd.DataFrame):
    timed = frame.loc[frame["timing_eligible"], "closure_seconds"]
    n, closed, eligible = len(frame), int(frame["is_closed"].sum()), len(timed)
    return {
        "requests": n, "closed_status": closed, "not_closed_status": n - closed,
        "timing_eligible": eligible, "closed_excluded_from_timing": closed - eligible,
        "closed_status_share": closed / n if n else None,
        "median_hours": number(timed.median() / 3600),
        "p90_hours": number(timed.quantile(.9) / 3600),
        "mean_hours": number(timed.mean() / 3600),
        "within_24h": int(timed.le(86400).sum()),
        "within_24h_share_of_eligible": float(timed.le(86400).mean()) if eligible else None,
        "zero_duration": int(timed.eq(0).sum()),
        "upper_iqr_outliers": int(frame["upper_iqr_outlier"].sum()),
        "unknown_zip": int(frame["incident_zip"].isna().sum()),
        "invalid_nonmissing_zip": int((frame["incident_zip"].notna() & ~frame["zip_valid"]).sum()),
        "negative_duration": int(frame["negative_duration"].sum()),
        "nonclosed_with_close_date": int((~frame["is_closed"] & frame["closed_date_local"].notna()).sum()),
    }


def group_metrics(frame, column):
    rows = [{"name": str(name), **metrics(group)} for name, group in frame.groupby(column, observed=True, sort=True)]
    return sorted(rows, key=lambda row: (-row["requests"], row["name"]))


def duration_bins(frame):
    times = frame.loc[frame["timing_eligible"], "closure_seconds"]
    bins = pd.cut(times, BIN_EDGES, labels=BIN_LABELS, right=True, include_lowest=True)
    counts = bins.value_counts(sort=False)
    return [{"label": label, "requests": int(counts.get(label, 0))} for label in BIN_LABELS]


def view_data(frame):
    daily = frame.groupby("created_day", observed=True).size()
    hours = frame.groupby("created_hour", observed=True).size()
    return {"metrics": metrics(frame), "daily": [{"day": f"2024-01-{day:02}", "requests": int(daily.get(f"2024-01-{day:02}", 0))} for day in range(1, 32)],
            "hourly": [{"hour": h, "requests": int(hours.get(h, 0))} for h in range(24)],
            "problems": group_metrics(frame, "problem_clean"),
            "channels": group_metrics(frame, "channel_clean"),
            "statuses": [{"name": str(k), "requests": int(v)} for k, v in frame["status_clean"].value_counts().items()],
            "duration_bins": duration_bins(frame)}


def build_outputs(raw, manifest, output: Path):
    output.mkdir(parents=True, exist_ok=True)
    frame, audit, quarantine = clean_data(raw, manifest)
    agencies = sorted(frame["agency_clean"].unique().tolist())
    boroughs = sorted(frame["borough_clean"].unique().tolist())
    views = {}
    for agency in ["all", *agencies]:
        subset = frame if agency == "all" else frame.loc[frame["agency_clean"].eq(agency)]
        for borough in ["all", *boroughs]:
            selected = subset if borough == "all" else subset.loc[subset["borough_clean"].eq(borough)]
            views[agency + "|" + borough] = view_data(selected)
    # Fix the visible hypothesis checks before writing any findings: same problem
    # across boroughs, never a pooled cross-agency performance league table.
    problems = group_metrics(frame, "problem_clean")
    comparisons = {row["name"]: group_metrics(frame.loc[frame["problem_clean"].eq(row["name"])], "borough_clean") for row in problems[:3]}
    top = frame.loc[frame["timing_eligible"]].sort_values(["closure_seconds", "unique_key"], ascending=[False, True]).head(12)
    outlier_examples = [{"request_id": str(r.unique_key), "agency": str(r.agency_clean), "problem": str(r.problem_clean),
                         "status": str(r.status_clean), "created": r.created_date_local.isoformat(), "closed": r.closed_date_local.isoformat(),
                         "closure_days": float(r.closure_seconds / 86400), "is_global_upper_iqr_outlier": bool(r.upper_iqr_outlier)} for r in top.itertuples()]
    full = metrics(frame)
    no_upper = metrics(frame.loc[~frame["upper_iqr_outlier"]])
    no_zero = metrics(frame.loc[~(frame["timing_eligible"] & frame["closure_seconds"].eq(0))])
    model = {"cohort": "Requests created 1–31 January 2024", "snapshot_utc": manifest["retrieval_finished_utc"],
             "source_url": manifest["landing_url"], "source_raw_sha256": manifest["raw_sha256"],
             "agencies": agencies, "boroughs": boroughs, "views": views,
             "agency_summary": group_metrics(frame, "agency_clean"), "borough_summary": group_metrics(frame, "borough_clean"),
             "same_problem_comparisons": comparisons, "quality": audit,
             "outlier_examples": outlier_examples, "sensitivity": {"all_eligible": full, "excluding_upper_iqr_outliers_diagnostic_only": no_upper, "excluding_zero_duration_diagnostic_only": no_zero}}
    write_json(output / "analysis.json", model)
    write_json(output / "quality.json", audit)
    for name, rows in [("agencies", model["agency_summary"]), ("boroughs", model["borough_summary"]), ("problems", problems), ("daily", views["all|all"]["daily"]), ("closure_distribution", duration_bins(frame))]:
        pd.DataFrame(rows).to_csv(output / (name + ".csv"), index=False, lineterminator="\n")
    pd.DataFrame(outlier_examples).to_csv(output / "outlier_examples.csv", index=False, lineterminator="\n")
    quarantine.to_csv(output / "quarantine.csv", index=False, lineterminator="\n")
    sample_cols = ["unique_key", "agency_clean", "problem_clean", "borough_clean", "status_clean", "created_day", "created_hour", "closure_seconds", "timing_eligible", "upper_iqr_outlier", "zip_valid"]
    frame.loc[:, sample_cols].head(20).to_csv(output / "clean_sample.csv", index=False, lineterminator="\n")
    return frame, model


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "results")
    args = parser.parse_args()
    raw, manifest = read_snapshot()
    _, model = build_outputs(raw, manifest, args.output)
    print(json.dumps({"raw_rows": len(raw), "metrics": model["views"]["all|all"]["metrics"], "filter_views": len(model["views"])}))


if __name__ == "__main__":
    main()
