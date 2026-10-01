# Cleaning decisions and measurement contract

The pinned raw source is never edited. `analysis.py` records before/after diagnostics in `results/quality.json`; `validate.py` separately recomputes them from raw CSV. Synthetic fixtures test situations absent from this snapshot.

| Issue | Policy | Actual snapshot evidence | Reason / limitation |
|---|---|---|---|
| Input types | Read all 14 columns as Pandas strings with default NA guessing disabled | Raw dtype audit included | IDs and ZIPs are labels, not numeric measures; explicit missingness is auditable |
| Whitespace | Strip leading/trailing whitespace and collapse internal runs | 24 descriptor cells changed | Formatting normalization only; no merging of supposed synonyms |
| Null values | Case-insensitive tokens: empty, NA, N/A, NULL, &lt;NA&gt; become missing | Descriptor missing rises from 1,706 blanks to 7,466 normalized missing; location type 33,625 to 33,632 | Tokens represent absent labels under this stated policy; no imputation; retain raw values for review |
| Exact repeats | Detect across every original selected field; keep one | 0 removed | Avoid repeated extraction rows; not the same as repeated real incidents |
| Conflicting request IDs | After exact deduplication, quarantine every row with a repeated nonmissing ID | 0 rows / 0 IDs | No trustworthy last-update rule is available; never choose an arbitrary version |
| Bad ID / creation date / cohort | Quarantine invalid numeric-text ID, invalid creation date, or date outside the selected creation cohort | All 0; 287,186 accepted | A valid key and cohort membership are required for request reporting |
| ZIP | Keep text; flag nonmissing values not matching five digits | 3,090 missing; 0 invalid nonmissing | Preserve leading zeroes; do not infer geography or drop otherwise usable requests |
| Borough | Normalize known names; UNSPECIFIED/null → Unknown / unassigned; retain unexpected labels and flag | 193 unassigned; 0 unexpected | Missing geography remains visible in volume |
| Agency/status/channel | Uppercase normalized labels; missing → Unknown | Null audit included | Stable grouping; no unseen value is silently discarded |
| Dates | ISO8601 coercion with failure flags; keep original text and parsed columns | 0 parse failures in all four date fields | Coercion is acceptable only with counts and retained raw values |
| Timezone | Treat floating source dates as America/New_York local; convert to UTC; ambiguous/nonexistent DST instants become unusable | 0 unresolved actual instants; synthetic DST cases tested | Real elapsed intervals can differ from naive wall-clock subtraction across DST |
| Missing closure | Keep in volume; exclude from timing | 2,961 missing closure dates total, including 1,280 Closed records | No source evidence supports imputation or setting closure to snapshot |
| Status/date contradiction | Flag non-Closed records with a close date; exclude all non-Closed from timing | 208 records; 75 negative intervals are within non-Closed statuses | A close timestamp does not override the current status |
| Negative/future closure | Keep volume, flag, exclude from timing | 75 negative; 0 future | Cannot represent credible elapsed closure; unknown correction must not be invented |
| Zero duration | Keep valid Closed pairs | 3,809 eligible zero durations | Could represent immediate or administrative closure; synthetic test protects inclusion |
| Long duration | Flag eligible values above global Q3 + 1.5 × IQR; retain and trace | Fence 769,379.5 seconds / 8.90 days; 49,374 flags | IQR is a diagnostic, not an error detector. The same whole-cohort fence is used for filtered views |
| Due date | Audit missingness, do not compute SLA compliance | 285,757 missing / 99.50% | Source dictionary calls it expected agency update date, not universal resolution deadline |
| Timing population | Closed + two usable UTC dates + nonnegative duration + closure no later than retrieval start | 284,017 eligible; 285,297 recorded Closed | Conditional closure statistics exclude censoring and missing/unusable times; not all-request resolution estimates |

## Features and aggregation

- `created_day`, `created_hour`, `created_weekday`, `created_weekend`: local intake timing, useful for volume inspection. No annual seasonality claim.
- `closure_seconds`: UTC-adjusted interval from created to closed timestamp, not time to a proven repair.
- `is_closed`, `negative_duration`, `future_close`, `timing_eligible`, `upper_iqr_outlier`, `zip_valid`: measurement gates and audit flags.
- Request count uses all accepted records in the selected scope. A unique request ID does not imply a unique incident or person.
- Median, mean, P90, and within-24-hour share use timing-eligible records only. P90/IQR use linear quantile interpolation. Inclusive threshold is ≤86,400 seconds; it is exploratory, not contractual.
- Duration bins have inclusive upper bounds: 0–1 hour, >1–24 hours, >1–7 days, >7–30 days, >30–90 days, >90 days. Zero is included in the first bin.
- Grouped timing denominators and all-request category shares are both explicit. Empty timing populations produce null, displayed as an em dash rather than zero.
- Agency/borough filters apply together to all explorer slice metrics and exports. Global quality/sensitivity/same-problem tables are separate and clearly labeled.

## Changes deliberately avoided

No missing-date, ZIP, or category-value inference; no blanket row removal for incomplete fields; no fabricated duplicate cases in real findings; no trimming of valid outliers; no inferred SLA; no causal rankings; no live-source refresh during normal analysis. These policies make the retained counts and the meaning of the estimates reviewable.
