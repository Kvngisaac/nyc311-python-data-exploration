# Verification and remaining gaps

## Completed computational checks

- The included raw ZIP and its single CSV member pass archive integrity, schema, row count, and SHA-256 checks.
- Official source-side total, agency/borough/status cells, and daily counts are compared with the raw source, independently of Pandas outputs. Exact queries/responses are retained.
- An independent stdlib validator recomputes published metrics from the raw CSV without importing the Pandas cleaner: 38,284 scalar comparisons, 8,105 distribution counts, all 105 filter views, all published agency/borough/problem/channel metrics, source quality audits, three same-problem comparisons, three sensitivity views, and 12 longest-duration traces.
- Six synthetic boundary tests cover duplicate conflicts, invalid IDs/dates/cohort, missing/negative/future/zero timing, ZIP/null/whitespace decisions, DST, inclusive duration bins, and empty denominators.
- Publication assertions verify narrative counts, rounded findings, denominators, concentration shares, sensitivity figures, borough comparisons, and the longest trace against exact model values.
- All five exported Matplotlib figures were visually inspected. Their values come from validated aggregates. PNG and SVG outputs are included.
- The notebook's Python cells are actually executed by the included CPython shared-namespace runner, with captured outputs and five rich image outputs. A Jupyter kernel is not used.
- JavaScript tests execute the real explorer handlers in a Node DOM harness across all 105 agency/borough combinations. They compare metrics, exact tables, complete category/channel exports, empty behavior, reset/focus, global-table scope, CSV quoting and formula-safe text with Python output. This is automated handler evidence, not a browser screenshot.
- Reproduction uses the pinned source offline. Fresh-extraction checks and publication/repository receipts are reported alongside the finished release, without inventing future deployment results in this document.

Machine-readable evidence: `results/validation.json`, `results/publication-checks.json`, `results/interaction-validation.json`, `results/notebook-execution.json`, `results/reproduction.json`. Test outputs are reproducible; no test fixtures enter real findings.

## What remains unverified

1. **Real-world correctness of agency records:** the dates, statuses, and categories match this snapshot; actual repair events, severity, status histories, and resident outcomes were not confirmed with NYC agencies.
2. **An all-request time-to-resolution estimate:** non-Closed and missing-date records are excluded from timing; censoring/selection are documented, not solved with a survival analysis. No SLA or causal performance conclusion is claimed.
3. **Live portfolio browser behavior:** supervised browser preview is unavailable for this static Site. Native desktop/mobile rendering, keyboard/select behavior, zoom, screen readers, cross-browser differences, authenticated asset/route loading, and actual browser download opening are not independently exercised. Static paths, data, DOM handlers, and deployment status are checked separately.
4. **Cold setup on other machines:** execution is checked with the documented installed Linux/Python environment, including a fresh source extraction. A fresh dependency installation, Windows/macOS reproduction, and every Python/Node version are not tested.
5. **Jupyter UI/kernel execution:** the notebook is valid nbformat4 JSON and its Python cells execute with the included runner; opening/running through Jupyter itself is not checked here.
6. **Employer access:** private Site/repository access is preserved. An external employer's account/login/access is not tested, and access must be granted deliberately before sharing private links with them.

Later source refreshes are not assumed to match this pin. The candidate-download helper intentionally does not overwrite it. Slot 04 is outside this project's scope and was not started.
