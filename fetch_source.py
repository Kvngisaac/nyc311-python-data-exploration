"""Fetch a fresh candidate without changing the pinned source or published results.

The original exact query and source-side controls are recorded in source/*.json.
Normal reproduction is offline. Use this command only for a deliberate refresh review.
"""
import csv
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import urllib.request

ROOT = Path(__file__).resolve().parent


def main():
    manifest = json.loads((ROOT / "source/manifest.json").read_text())
    target = ROOT / "work" / ("candidate-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"))
    target.mkdir(parents=True, exist_ok=False)
    started = datetime.now(timezone.utc).isoformat()
    request = urllib.request.Request(manifest["query_url"], headers={"User-Agent": "nyc311-portfolio-reproducibility/1.0"})
    with urllib.request.urlopen(request, timeout=180) as response:
        payload = response.read()
        headers = dict(response.headers)
    rows = csv.DictReader(io.StringIO(payload.decode("utf-8-sig")))
    if rows.fieldnames != manifest["fields"]:
        raise ValueError("Candidate schema changed; pinned files remain unchanged")
    count = sum(1 for _ in rows)
    if count >= manifest["limit"]:
        raise ValueError("Candidate may be truncated; refresh requires pagination review")
    digest = hashlib.sha256(payload).hexdigest()
    (target / "candidate.csv").write_bytes(payload)
    receipt = {"query_url": manifest["query_url"], "retrieval_started_utc": started,
               "retrieval_finished_utc": datetime.now(timezone.utc).isoformat(),
               "headers": headers, "rows": count, "raw_sha256": digest,
               "matches_pinned_raw": digest == manifest["raw_sha256"],
               "warning": "Candidate only. No pinned source or analysis was overwritten. Revalidate server counts, schema, cleaning, and conclusions before adopting."}
    (target / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({"candidate_directory": str(target), "rows": count, "matches_pinned_raw": receipt["matches_pinned_raw"]}))


if __name__ == "__main__":
    main()
