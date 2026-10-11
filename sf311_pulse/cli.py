"""Command-line entry point for the 311 pipeline."""

import argparse
import json
from pathlib import Path

from .pipeline import load_csv, store, summarize


def main() -> None:
    parser = argparse.ArgumentParser(description="Load a 311 CSV into SQLite and print a summary.")
    parser.add_argument("--input", type=Path, default=Path(__file__).parent / "data" / "sample_requests.csv", help="Input CSV (defaults to bundled offline sample).")
    parser.add_argument("--database", type=Path, default=Path("sf311-pulse.sqlite"), help="SQLite database path.")
    args = parser.parse_args()
    records, rejected = load_csv(args.input)
    store(records, args.database)
    report = summarize(args.database)
    report.update({"loaded_from_input": len(records), "rejected_rows": rejected, "database": str(args.database)})
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
