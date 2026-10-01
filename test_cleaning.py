"""Synthetic boundary fixtures; these records are never mixed into real findings."""
import importlib.util
from pathlib import Path
import unittest

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("eda", ROOT / "analysis.py")
eda = importlib.util.module_from_spec(spec)
spec.loader.exec_module(eda)
FIELDS = ["unique_key", "created_date", "closed_date", "agency", "agency_name", "complaint_type", "descriptor", "location_type", "incident_zip", "borough", "status", "due_date", "resolution_action_updated_date", "open_data_channel_type"]
MANIFEST = {"fields": FIELDS, "cohort_start": "2024-01-01", "cohort_end_exclusive": "2024-02-01", "retrieval_started_utc": "2026-10-01T00:00:00+00:00"}


def record(key="1", **changes):
    row = dict.fromkeys(FIELDS, "")
    row.update(unique_key=key, created_date="2024-01-01T00:00:00.000", closed_date="2024-01-02T00:00:00.000", agency="TEST", agency_name="Test agency", complaint_type="Test problem", incident_zip="01234", borough="QUEENS", status="Closed", open_data_channel_type="ONLINE")
    row.update(changes)
    return row


def clean(rows):
    return eda.clean_data(pd.DataFrame(rows, columns=FIELDS).astype("string"), MANIFEST)


class CleaningBoundaries(unittest.TestCase):
    def test_exact_and_conflicting_duplicates(self):
        a = record()
        frame, audit, quarantine = clean([a, a.copy(), record("2", descriptor="A"), record("2", descriptor="B")])
        self.assertEqual(audit["exact_duplicate_rows_removed"], 1)
        self.assertEqual(audit["conflicting_id_rows"], 2)
        self.assertEqual(audit["conflicting_unique_ids"], 1)
        self.assertEqual(frame.unique_key.tolist(), ["1"])
        self.assertEqual(len(quarantine), 2)

    def test_bad_identity_and_creation_are_quarantined(self):
        frame, audit, quarantine = clean([record(""), record("x"), record("3", created_date="broken"), record("4", created_date="2024-02-01T00:00:00"), record("005")])
        self.assertEqual(frame.unique_key.tolist(), ["005"])
        self.assertEqual(audit["quarantined_rows"], 4)
        self.assertEqual(len(quarantine), 4)

    def test_missing_and_contradictory_dates_keep_volume(self):
        frame, audit, _ = clean([record("1", closed_date=""), record("2", closed_date="2023-12-31T00:00:00"), record("3", status="Open"), record("4", closed_date="2027-01-01T00:00:00"), record("5")])
        self.assertEqual(len(frame), 5)
        self.assertEqual(frame.timing_eligible.tolist(), [False, False, False, False, True])
        self.assertEqual(audit["negative_duration_requests"], 1)
        self.assertEqual(audit["future_close_requests"], 1)
        self.assertEqual(eda.metrics(frame)["closed_excluded_from_timing"], 3)

    def test_types_null_tokens_and_leading_zero_zip(self):
        frame, audit, _ = clean([record("0001", descriptor="  N/A  ", borough="Unspecified", incident_zip="01234"), record("2", incident_zip="1234.0", descriptor="  Pipe   leak  ")])
        self.assertEqual(frame.unique_key.iloc[0], "0001")
        self.assertEqual(frame.incident_zip.iloc[0], "01234")
        self.assertTrue(pd.isna(frame.descriptor.iloc[0]))
        self.assertEqual(frame.descriptor.iloc[1], "Pipe leak")
        self.assertEqual(frame.borough_clean.iloc[0], "Unknown / unassigned")
        self.assertEqual(audit["invalid_nonmissing_zip_requests"], 1)
        self.assertEqual(str(frame.created_hour.dtype), "Int64")

    def test_dst_and_zero_duration(self):
        frame, audit, _ = clean([record("1", closed_date="2024-03-10T03:00:00"), record("2", closed_date="2024-03-10T02:30:00"), record("3", closed_date="2024-11-03T01:30:00"), record("4", closed_date="2024-01-01T00:00:00")])
        self.assertEqual(frame.closure_seconds.iloc[0] / 3600, 69 * 24 + 2)
        self.assertEqual(frame.timing_eligible.tolist(), [True, False, False, True])
        self.assertEqual(audit["timezone_unresolvable_count"]["closed_date"], 2)
        self.assertEqual(eda.metrics(frame)["zero_duration"], 1)

    def test_duration_boundaries_and_empty_denominators(self):
        frame, _, _ = clean([record("1", closed_date="2024-01-01T01:00:00"), record("2"), record("3", closed_date="2024-01-08T00:00:00"), record("4", status="Open", closed_date="")])
        self.assertEqual([x["requests"] for x in eda.duration_bins(frame)], [1, 1, 1, 0, 0, 0])
        self.assertEqual(eda.metrics(frame)["within_24h"], 2)
        empty = eda.metrics(frame.loc[frame.agency_clean.eq("absent")])
        self.assertEqual(empty["requests"], 0)
        self.assertIsNone(empty["median_hours"])
        self.assertIsNone(empty["within_24h_share_of_eligible"])


if __name__ == "__main__":
    unittest.main()
