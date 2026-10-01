# Interview brief: understand and defend the NYC311 project

This is a teaching guide for Justin Pierite. The implementation was AI-assisted; do not claim to have typed every line or independently authored the complete solution. Practice running the project, explaining the decisions, and changing a small analysis yourself. A good interview answer is about the evidence and judgment you can personally defend.

## Your 60-second explanation

“I used 287,186 official NYC311 requests created in January 2024 to investigate demand concentration and whether the data supported trustworthy closure-time reporting. I preserved a checksummed raw snapshot, used Pandas to inspect and normalize types and missing values, separated request-volume records from timing-eligible records, and investigated date/status contradictions and long durations. The top three problem categories contributed 39.88% of requests. Among 284,017 eligible Closed records, the median closure time was 19.10 hours, but the mean was 317.63 hours because of the long tail. I retained valid outliers and showed sensitivity instead of deleting them. I independently reconciled the reported aggregates against raw CSV and built an explorer with consistent filters and exact tables. These are administrative closure measures, not proof of a repair or causal performance rankings.”

Use this only after you can explain each sentence. If asked about assistance, say which parts you reviewed, ran, and understand; credit AI assistance directly.

## Learn the source first

NYC311 routes service requests to city agencies. Each selected row has a request ID, creation/closure dates, agency, problem category, detail, location type, ZIP, borough, status, expected update date, latest resolution-action date, and submission channel. The raw API calls the problem field `complaint_type`, even though the display name is now Problem.

The cohort is “created during January 2024,” not “closed during January” and not “January's backlog.” The data was fetched on 1 October 2026. Some of those requests were closed much later. The source is mutable: a new download can revise historical values. A pinned ZIP and SHA-256 digest let a reviewer reproduce exactly the values used here.

This is one winter month, chosen as a coherent and manageable operational cohort, not a representative annual sample. There are no resident counts, severity measures, unique incident identifiers, satisfaction outcomes, or status histories. Two distinct request IDs could concern the same problem. That distinction prevents you from calling the count “unique incidents.”

## The business question in plain language

Before a manager asks which agency is “fastest,” the analyst should check what “fast” measures and whether the dates can support it. This project asks where intake is concentrated, what the recorded closure distribution looks like, and where missing or contradictory fields need an audit.

Useful proposed actions: review the largest problem categories; show distribution plus eligibility coverage; ask agency data owners about contradictory statuses and dates; inspect same-problem comparisons and long-duration traces. No intervention was performed, no business outcome was measured, and no staffing recommendation was optimized.

## Cleaning decisions you must be able to defend

**Why strings first?** An ID or ZIP is a label. Numeric inference could drop leading zeroes; default missing-token inference can conceal what the source supplied. `pd.read_csv(..., dtype='string', keep_default_na=False)` preserves the original representation.

**How did you handle missingness?** Inspect raw blanks first, then strip whitespace and normalize a declared token list. Descriptor has 1,706 literal blanks but 7,466 normalized missing values; that shows why the policy matters. Missing labels can be Unknown in grouping, but missing closure dates are never imputed. A field can be missing without making the entire request useless.

**What happened to duplicates?** `duplicated()` over every raw selected field identifies exact repeats. `duplicated(keep=False)` on request IDs after exact deduplication identifies conflicting versions. There are zero of both in this snapshot. Synthetic tests prove the policy handles them. Similar categories/dates are not enough to call two requests duplicates.

**Which rows were dropped?** None from actual request volume: all 287,186 pass key/date/cohort gates. The pipeline would quarantine invalid or conflicting IDs and invalid/out-of-cohort creation dates. Keep this distinct from closure-time exclusions.

**Why two denominators?** Volume counts every accepted request. Timing uses only recorded Closed with valid paired dates and nonnegative, nonfuture elapsed time. There are 285,297 Closed records but only 284,017 timing-eligible records because 1,280 Closed records lack closure dates. The 75 negative intervals all have non-Closed status, so subtracting another 75 from the Closed denominator would be wrong.

**Why timezone conversion?** Source dates are local floating timestamps. Localize to America/New_York and convert to UTC before subtraction so crossing daylight-saving changes reflects elapsed time. Do not shift or guess ambiguous/nonexistent local instants. Actual snapshot dates have no unresolved cases; synthetic cases test that boundary.

**Why not delete outliers?** Above Q3 + 1.5 × IQR is a statistical flag, not a factual error. The fence is 8.90 days, flagging 49,374 eligible records. Removing them changes mean from 317.63 to 28.09 hours and median from 19.10 to 6.71, which changes the population being summarized. Keep them, trace the longest, and ask a data owner about the administrative process. Also retain 3,809 zero durations because instantaneous administrative closure can be valid.

**Can due_date measure SLA compliance?** No. Its dictionary meaning is expected agency update date, and it is 99.50% missing. An SLA rate would need agency-specific definitions and valid coverage. The 24-hour proportion is simply an exploratory threshold.

## Pandas techniques: connect the operation to its purpose

| Technique | Where to find it | What it accomplishes |
|---|---|---|
| `.copy()`, `.duplicated()`, `.drop_duplicates()` | `clean_data()` | Preserve source and apply explicit repeat policy |
| `.str.strip()`, regex replace, `.mask()`, `.isna()` | Column normalization | Standardize representation with before/after missingness |
| `.str.fullmatch()` and boolean masks | ID/ZIP and quarantine gates | Audit validity without numeric coercion or invented values |
| `pd.to_datetime(errors='coerce')` | Date parsing | Convert only parseable dates and count failures |
| `.dt.tz_localize()` / `.dt.tz_convert()` | Date parsing | Distinguish local calendar features from actual elapsed time |
| `.dt.hour`, `.dt.day_name()`, `.dt.dayofweek` | Features | Create useful local intake attributes |
| `.loc[mask]` and vectorized date subtraction | Eligibility / metrics | Make the measurement population explicit |
| `.groupby(..., observed=True)` | `group_metrics()` | Compute consistent category metrics and sample sizes |
| `.median()`, `.mean()`, `.quantile()` | `metrics()` / IQR | Summarize distribution and define transparent diagnostics |
| `pd.cut(..., right=True, include_lowest=True)` | Duration bins | Assign inclusive intervals including zero |
| `.reindex()` and stable sorting | Daily/hourly summaries | Include zero-count periods and deterministic presentation |

Start reading `read_snapshot()`, then `clean_data()`, then `metrics()`, `view_data()`, and `main()`. Do not memorize syntax without understanding the denominator. The notebook breaks this into inspection, missingness, cleaning, grouping, outliers, sensitivity, and chart cells.

## Findings you can explain without overclaiming

1. HEAT/HOT WATER (51,325), Illegal Parking (41,124), and Noise - Residential (22,091) sum to 114,540 / 287,186 = 39.88%. This is demand concentration in records, not prevalence of city problems.
2. The timing median is 19.10 hours and P90 668.55 hours, compared with mean 317.63. A right tail can pull the mean upward. Present both typical and tail behavior with timing n=284,017.
3. Within 24 hours: 152,789 / 284,017 = 53.80%. Say “eligible recorded closures,” not “all problems fixed within a day.”
4. Status/date inconsistencies need an audit. 208 non-Closed records contain a closure timestamp; 75 have negative intervals. Missing-date Closed records remain part of intake volume.
5. HEAT/HOT WATER borough medians span 29.59 hours in the Bronx to 45.48 in Manhattan. Same-category comparisons reduce one aspect of mix, but do not control severity or administrative workflow. Do not say one borough performs better.
6. The longest trace, request 59916703, has valid source dates spanning about 984.93 days. Those dates are verified against the snapshot; actual repair history is not verified.

## Validation: what was actually checked?

`analysis.py` uses Pandas. `validate.py` independently uses CSV readers, Python datetimes/zoneinfo, counters, and a separate quantile implementation. It does not import the Pandas cleaner. It checks 38,284 scalar comparisons and 8,105 distribution counts, all 105 agency/borough views, group metrics, three sensitivity policies, three same-problem comparisons, quality audits, and 12 source traces. This is much stronger than comparing two charts built from the same output.

Six synthetic tests exercise duplicate conflicts, invalid keys/cohort dates, missing/negative/future intervals, ZIP/null/whitespace policy, daylight-saving/zero durations, and inclusive bins/empty denominators. They are clearly separated from real findings.

Server-side total, agency/borough/status cells, and daily counts are compared with the raw snapshot. The normal run is offline and checks hashes. The release is reproduced from a fresh extraction and generated data/figures are compared. A JavaScript DOM event harness checks all filter combinations, exact values/tables, empty/reset behavior, and exported CSV. Export text protects against formula execution.

Limits: matching calculations does not verify that an agency's record reflects reality; independent code can still share a flawed business definition, so the measurement contract is documented. Browser rendering, native keyboard behavior, mobile/zoom, assistive technology, authenticated deployment asset loading/downloads, cold dependency installation, and actual Jupyter UI execution are not independently established here. The notebook's Python cells are executed by the included runner, not a Jupyter kernel.

## Likely questions and answer guidance

**“Why this project instead of another retail example?”** It tests real operational measurement, missing values, timestamps, categorical aggregation, outlier judgment, and reproducibility on a different official source.

**“How do you know the data is complete?”** The query defines a whole creation cohort and sorts IDs; the response count matches the official server count, grouped cells, and daily controls. Schema, archive integrity, and hashes are checked. This establishes completeness for that selected query, not that every real-world problem was reported to 311.

**“Why not just call `dropna()`?”** It would throw away valid intake records because optional details/geography are missing and silently bias reporting. Missingness is handled per field and purpose.

**“Why no predictive model?”** The task is an EDA/measurement audit. Targets and histories do not establish service outcomes; trustworthy descriptive reporting is a more defensible deliverable here.

**“How would you improve the analysis?”** Confirm status semantics with agencies, obtain history/severity/incident linkage, add more months and population/context denominators, analyze censored times appropriately, stratify comparable process categories, and define agency-specific service targets. Those are proposed extensions, not completed checks.

**“What if the source changes tomorrow?”** Normal reproduction uses the included pin. Refresh downloads a separate candidate and reports its hash/count. Review schema, source controls, and changed outcomes before publishing a new version.

**“How would you scale it?”** Select only needed columns, use vectorized operations and group aggregation, consider chunked ingestion/Parquet or a database for larger cohorts, preserve a validation reference, and measure memory/runtime. This project has not benchmarked a production-scale architecture.

**“What was the hardest judgment?”** Separating volume from timing populations and deciding not to delete statistically unusual but chronologically valid records. Explain how those choices change the conclusions.

**“What did you personally do, and what did AI do?”** Be precise about your own review, execution, learning, and modifications. The implementation was AI-assisted; do not invent personal authorship or learning already completed. Demonstrate understanding by tracing a function and changing a grouping live.

## Practice before using it in an interview

- Run `python reproduce.py` and explain each output.
- Open the notebook and identify the raw, accepted, Closed, and timing-eligible counts.
- Filter the explorer to one agency/borough and explain why coverage changes.
- Trace one outlier back to raw source dates and explain why chronology does not verify a fix.
- Add a weekend/weekday volume grouping yourself; validate that its counts sum to the full cohort.
- Explain one reason the borough comparison could be confounded.
- Answer the assistance question honestly and distinguish verified calculations from unverified live browser behavior.

You are ready to present the case study when you can reason through these decisions without reading this guide verbatim.
