# NYC311: Python data exploration

**An operations measurement audit and exploratory analysis of 287,186 official service requests.** This project demonstrates how to turn imperfect administrative data into reproducible reporting without hiding missing values, inventing dates, or treating an administrative closure as proof of a fix.

[Interactive portfolio explorer](https://justin-pierite-data-work.kvngisaa.chatgpt.site/python-exploration/) · [Employer case study](CASE_STUDY.md) · [Cleaning decisions](CLEANING_DECISIONS.md) · [Interview brief](INTERVIEW_BRIEF.md) · [Verification and remaining gaps](VERIFICATION.md)

The portfolio and this repository are private; permission is required. This is historical public-data portfolio work, not work performed for NYC or an employer. Implementation was AI-assisted. The interview brief is intended to help the portfolio owner explain and defend the work personally.

## Business problem

An operations analyst needs to decide which request categories deserve review and whether the underlying fields support trustworthy timing comparisons. The analysis examines demand concentration, date/status consistency, missingness, conditional closure-time distributions, and comparisons within the same problem category. It supports review priorities and questions for data owners; it does not claim improved service outcomes or optimal staffing.

## Verified findings

| Measure | Result | Denominator / meaning |
|---|---:|---|
| Requests created in January 2024 | 287,186 | Full accepted creation cohort |
| HEAT/HOT WATER + Illegal Parking + Noise - Residential | 114,540 / 39.88% | Share of all accepted requests |
| Recorded Closed | 285,297 | Administrative status at the October 2026 snapshot |
| Usable closure-time records | 284,017 | Closed, usable dates, nonnegative elapsed UTC time, no future closure |
| Median / mean / P90 recorded closure | 19.10 / 317.63 / 668.55 hours | Timing-eligible records; not time to a verified fix |
| Within 24 hours | 152,789 / 53.80% | Of timing-eligible records; exploratory threshold, not an SLA |
| Closed records without a closure date | 1,280 | Remain in volume; excluded from timing |
| Negative date intervals | 75 | All are non-Closed; not an additional 75 excluded Closed records |
| Global upper-IQR flags / zero durations | 49,374 / 3,809 | Both remain in default eligible timing metrics |
| Exact duplicate rows / conflicting IDs | 0 / 0 | Audited; no duplicates invented for demonstration |

The long tail explains why the mean is much higher than the median. Removing upper-IQR flags would change the median to 6.71 hours and mean to 28.09 hours; that sensitivity is documented, not adopted as the cleaning policy. Same-problem borough comparisons remain descriptive because severity, reporting behavior, and administrative process are not controlled.

## Reproduce offline

Tested with CPython 3.12.14, Pandas 2.2.3, NumPy 2.3.5, Matplotlib 3.10.8, tzdata 2026.4, and Node.js for interaction checks. No API key, database, notebook server, or network request is needed to reproduce the included snapshot.

```bash
python -m venv .venv
# Linux/macOS:
source .venv/bin/activate
# Windows PowerShell alternative: .venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python reproduce.py
```

`reproduce.py` runs the Pandas analysis, independent raw-CSV validator, six synthetic boundary tests, five Matplotlib figures, the Python-cell notebook runner, publication assertions/source controls, and Node interaction tests when Node is available. Without Node, Python analysis still runs but JavaScript checks are explicitly marked skipped. This environment's verification includes Node.

Individual commands:

```bash
python analysis.py
python validate.py
python -m unittest discover -s tests -v
python visualize.py
python notebook.py
python build_site.py
node tests/explorer.test.cjs
```

Open `site/index.html` locally for the interactive explorer; all scripts and data are local. Its portfolio-back and portfolio ZIP links are intended for the hosted integration. Source and figures are also available directly in this repository. The hosted project ZIP includes this complete directory, including the compressed raw snapshot.

## Source and provenance

- Publisher: City of New York / NYC311.
- [311 Service Requests from 2020 to Present](https://data.cityofnewyork.us/Social-Services/311-Service-Requests-from-2020-to-Present/erm2-nwe9), dataset `erm2-nwe9`.
- Creation cohort: local `2024-01-01T00:00:00` inclusive to `2024-02-01T00:00:00` exclusive. All rows in that query, not a random sample.
- Retrieved 1 October 2026; exact request, time, source headers, field list, row count, and SHA-256 hashes are in [the manifest](source/manifest.json).
- Included 14 selected columns; no addresses, coordinates, or complaint narratives. Raw CSV: 65,348,448 bytes, compressed in `source/nyc311-2024-01.csv.zip`.
- Raw SHA-256: `ffaad5274e974cbece133dcf2c8576a96d15d9e6a1cafac9db112a7c2d7de19d`.
- Official dictionary descriptions: [schema.json](source/schema.json). Original server-side count/group/day controls: [remote-controls.json](source/remote-controls.json).
- The dataset changes over time. Normal runs use the pinned data; `fetch_source.py` downloads a fresh candidate to `work/` without overwriting the source or results. A changed candidate requires a new provenance/analysis review.
- Backend `complaint_type` / `descriptor` remain in the API even though the source display labels are now Problem / Problem Detail. See [official dataset updates](https://www.nyc.gov/opendata/news/all-news/311-Service-Requests-Updates).

## Inspect the evidence

| File / directory | Purpose |
|---|---|
| `analysis.py` | String-safe ingestion, normalization, audit flags, features, groups, quantiles, 105 filter views |
| `validate.py` | Independent stdlib CSV/datetime/zoneinfo reference, no Pandas cleaning code |
| `tests/` | Cleaning boundary cases and JavaScript interaction/export tests |
| `notebooks/nyc311_exploration.ipynb` | Step-by-step inspection, cleaning, EDA, and visual evidence |
| `results/` | Exact aggregate JSON/CSVs, quality audit, validation evidence, longest-duration traces |
| `results/clean_sample.csv` | First 20 cleaned rows for inspection, not a random sample or analysis input |
| `figures/` | Five exact-data PNG/SVG charts |
| `site/` | Static browser explorer, native filters, complete tables, scope-aware CSV export |
| `INTERVIEW_BRIEF.md` | Teaching notes, code techniques, questions, answer guidance, defense checklist |

## Limitations and rights

One winter-month creation cohort is not an annual demand model. Requests are not unique people or incidents, and there is no population denominator. Status/timestamps reflect administrative records, may be updated, and have not been confirmed with the agencies. The timing population excludes non-Closed requests and missing/unusable closure dates; censoring and selection prevent an unbiased all-request time-to-resolution claim. Due date is an expected update date and is mostly missing, so no deadline-compliance rate is calculated. No causal impact, service effectiveness, or resident satisfaction is established.

Code and original project documentation: MIT ([LICENSE](LICENSE)). NYC source data and derived data remain subject to [NYC Open Data terms](https://data.cityofnewyork.us/stories/s/Terms-of-Use/k9k7-3cje). Source attribution and modifications are documented; no endorsement or accuracy warranty is implied.
