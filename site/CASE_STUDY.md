# NYC311: build a trustworthy operations report before ranking performance

**Business audience:** an operations manager and the analyst responsible for service-request reporting.

**Question:** Where does intake concentrate, what does recorded closure time look like, and which data-quality issues would make a performance comparison unreliable?

## Why this dataset

NYC311 is an official, large administrative source with operational categories, agencies, timestamps, locations, statuses, and submission channels. A complete January 2024 creation cohort offers enough observations to inspect real missing values, contradictory timestamps, and long-tail behavior while remaining reproducible on a normal analyst workstation. It is unrelated to the retail portfolio study and tests different measurement judgments.

The selected snapshot contains 287,186 rows and 14 fields, retrieved on 1 October 2026. This is a cohort of requests created in January 2024, observed at a later snapshot; closure events are not restricted to January. The original source and retrieval query are pinned with hashes. No addresses, coordinates, or narratives are selected.

## Method and important decisions

1. Read all raw columns as strings and inspect schema, row count, blanks, example values, and duplicate IDs before inferring types.
2. Preserve the raw archive. Normalize whitespace and a declared list of null tokens. Keep IDs/ZIP codes as strings; do not infer missing geography.
3. Detect exact repeats and conflicting IDs separately. Exact repeats would be removed once; all versions of a conflicting ID would be quarantined. Both counts are zero in this actual cohort.
4. Parse dates with coercion and audit parse failures. Interpret floating dates as New York local time, convert to UTC for elapsed intervals, and refuse to guess ambiguous/nonexistent daylight-saving instants. Creation-day/hour features use local time.
5. Retain all accepted records in request-volume analysis. Require Closed status plus usable, chronologically valid date pairs for closure-time metrics. Do not fill missing closure dates with means or the snapshot date.
6. Investigate zero and long durations. Keep valid values, trace the longest back to original records, and show how trimming changes the answer. The global IQR fence is a review flag, not proof of error.
7. Group by agency, borough, problem, channel, creation day/hour, and recorded status. Report medians/P90 and denominators, and compare locations within the same problem before discussing mixed populations.
8. Recalculate the published aggregates independently from the raw CSV using stdlib code. Test cleaning edge cases and every agency/borough interaction; compare the source-side counts with the retrieved records.

## Findings and defensible actions

| Evidence | Implication | Proposed action, not a claimed outcome |
|---|---|---|
| The top three problems total 114,540 requests, 39.88% of intake; HEAT/HOT WATER contributes 51,325 | A small category set accounts for a substantial share of reporting workload | Begin category-level review here; seek incident deduplication and seasonality evidence before allocating resources |
| Median recorded closure is 19.10 hours; mean is 317.63 and P90 is 668.55, across 284,017 eligible records | The distribution is strongly asymmetric; a single mean is an incomplete operational summary | Show median, tail measure, eligibility coverage, and category mix together |
| 1,280 Closed requests lack closure dates; 208 non-Closed requests have one; 75 intervals are negative, all non-Closed | A status filter alone cannot guarantee valid elapsed time | Audit status/timestamp consistency with data owners; preserve volume and disclose timing exclusions |
| 49,374 eligible rows exceed the 8.90-day global IQR fence; removing them changes mean to 28.09 hours | A blanket trimming rule changes the estimand substantially | Trace anomalies and confirm process semantics before deleting records |
| HEAT/HOT WATER eligible-record medians range from 29.59 hours in the Bronx to 45.48 in Manhattan | Even within one problem, observed location differences warrant investigation | Examine severity, subtypes, reporting behavior, repeat incidents, and agency workflows before a performance judgment |

The longest traced request, ID `59916703`, is a DOT Street Light Condition record created 3 January 2024 and marked closed 14 September 2026: approximately 984.93 elapsed days. The dates match the pinned raw record and chronology is valid. This does **not** prove a streetlight took that long to repair; agency confirmation and a status-history audit would be needed. See `results/outlier_examples.csv` for all 12 traces.

## Deliverable

The static interactive explorer has 14 agency options plus All, six borough options plus All, and all 105 combinations. KPIs, daily/hourly intake, all category and channel tables, statuses, duration bins, and CSV exports use the same selected scope. Global quality, sensitivity, and same-problem comparisons are explicitly labeled as unfiltered. Empty combinations show no estimate and disable export. Exact-value tables accompany visual summaries; CSV text is escaped for spreadsheet formulas.

Five downloadable Matplotlib figures cover demand mix, daily intake, duration distribution, missingness, and same-problem borough comparisons. Source, cleaning decisions, exact aggregates, validator, tests, notebook, and interview brief are included in the reproducible package.

## Evidence and bounds

The independent validator matches 38,284 scalar metrics and 8,105 distribution counts, all 105 filter views, quality audits, group metrics, three sensitivity views, three same-problem comparisons, and 12 outlier traces. Six synthetic cleaning boundary tests pass. Source-side totals and group/day counts are checked against the raw snapshot. The figures were visually inspected as exported images.

Calculations are verified against this snapshot, not certified against real-world outcomes. Browser rendering and native keyboard/mobile/assistive-technology behavior could not be exercised here. Exact remaining gaps and reproduction results are recorded in `VERIFICATION.md`.

No staffing optimum, seasonal trend, causal agency ranking, SLA compliance, repair-time estimate, or resident-satisfaction outcome is claimed. The useful result is an auditable measurement foundation and a defensible list of operational review questions.
