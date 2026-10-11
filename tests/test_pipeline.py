
from sf311_pulse.pipeline import load_csv, store, summarize


def test_load_validates_and_deduplicates_fixture():
    from pathlib import Path

    fixture = Path(__file__).parents[1] / "sf311_pulse" / "data" / "sample_requests.csv"
    rows, rejected = load_csv(fixture)
    assert len(rows) == 6
    assert rejected == 1
    assert len({row["service_request_id"] for row in rows}) == 6


def test_sqlite_upsert_is_idempotent_and_updates(tmp_path):
    database = tmp_path / "nested" / "requests.sqlite"
    row = {"service_request_id": "42", "requested_datetime": "2025-01-01T00:00:00", "agency": "DPW", "service_name": "Cleanup", "status": "Open", "neighborhood": "Mission"}
    assert store([row], database) == 1
    assert store([row], database) == 1
    changed = {**row, "status": "Closed"}
    assert store([changed], database) == 1
    report = summarize(database)
    assert report["total"] == 1
    assert report["statuses"] == {"Closed": 1}


def test_missing_required_column_is_clear(tmp_path):
    source = tmp_path / "invalid.csv"
    source.write_text("id\n1\n")
    try:
        load_csv(source)
    except ValueError as error:
        assert "missing required columns" in str(error)
    else:
        raise AssertionError("expected missing-column validation")
