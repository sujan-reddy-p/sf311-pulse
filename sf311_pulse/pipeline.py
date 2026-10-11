"""Load, validate, deduplicate, and summarize 311 request CSV data."""

from __future__ import annotations

import csv
import sqlite3
from datetime import datetime
from pathlib import Path

REQUIRED_COLUMNS = ("service_request_id", "requested_datetime", "agency", "service_name", "status", "neighborhood")


def load_csv(path: Path) -> tuple[list[dict[str, str]], int]:
    """Read records and count rows rejected for missing or invalid values."""
    latest: dict[str, dict[str, str]] = {}
    rejected = 0
    with path.open(newline="", encoding="utf-8-sig") as source:
        reader = csv.DictReader(source)
        if reader.fieldnames is None:
            raise ValueError("CSV has no header")
        missing = set(REQUIRED_COLUMNS) - set(reader.fieldnames)
        if missing:
            raise ValueError(f"CSV is missing required columns: {', '.join(sorted(missing))}")
        for row in reader:
            record = {key: (row.get(key) or "").strip() for key in REQUIRED_COLUMNS}
            try:
                datetime.fromisoformat(record["requested_datetime"].replace("Z", "+00:00"))
            except ValueError:
                rejected += 1
                continue
            if not all(record[key] for key in REQUIRED_COLUMNS):
                rejected += 1
                continue
            latest[record["service_request_id"]] = record
    return list(latest.values()), rejected


def store(records: list[dict[str, str]], database: Path) -> int:
    """Idempotently upsert records by their stable request ID."""
    database.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(database) as connection:
        connection.execute("""CREATE TABLE IF NOT EXISTS requests (
            service_request_id TEXT PRIMARY KEY, requested_datetime TEXT NOT NULL,
            agency TEXT NOT NULL, service_name TEXT NOT NULL, status TEXT NOT NULL,
            neighborhood TEXT NOT NULL)""")
        connection.executemany("""INSERT INTO requests VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(service_request_id) DO UPDATE SET
            requested_datetime=excluded.requested_datetime, agency=excluded.agency,
            service_name=excluded.service_name, status=excluded.status,
            neighborhood=excluded.neighborhood""",
            [tuple(record[key] for key in REQUIRED_COLUMNS) for record in records])
        return connection.execute("SELECT COUNT(*) FROM requests").fetchone()[0]


def summarize(database: Path) -> dict[str, object]:
    """Build compact counts from all records currently persisted."""
    with sqlite3.connect(database) as connection:
        total = connection.execute("SELECT COUNT(*) FROM requests").fetchone()[0]
        statuses = dict(connection.execute("SELECT status, COUNT(*) FROM requests GROUP BY status ORDER BY status"))
        neighborhoods = connection.execute("""SELECT neighborhood, COUNT(*) AS n FROM requests
            GROUP BY neighborhood ORDER BY n DESC, neighborhood LIMIT 5""").fetchall()
    return {"total": total, "statuses": statuses, "top_neighborhoods": neighborhoods}
