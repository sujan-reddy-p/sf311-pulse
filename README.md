# sf311-pulse

A tiny, local-first Python data engineering pipeline for exploring San Francisco 311 service requests. It demonstrates a repeatable extract/validate/deduplicate/load/report workflow using only the Python standard library and SQLite. A small representative fixture ships with the project, so the complete demo runs offline with no account, API key, or network access.

## Quick start

Requires Python 3.10 or newer.

```bash
python -m sf311_pulse.cli --database demo.sqlite
```

The command reads `sf311_pulse/data/sample_requests.csv`, validates required fields and ISO-8601 timestamps, keeps one record per service request ID, upserts into SQLite, and prints JSON totals, status counts, and the five busiest neighborhoods. Re-running it is safe: request IDs are primary keys and existing records are updated. The output database is created in the current directory.

Use a different CSV or database path:

```bash
python -m sf311_pulse.cli --input requests.csv --database requests.sqlite
```

The input CSV must contain `service_request_id`, `requested_datetime`, `agency`, `service_name`, `status`, and `neighborhood`. Invalid or incomplete rows are counted and skipped; missing required columns produce a clear error. Deduplication uses the last valid row for each ID in the input.

## Development

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -e '.[dev]'
pytest
```

## Data

The bundled eight-row sample (including a repeated ID and an invalid timestamp to illustrate data quality handling) is intentionally small and illustrative, not a current or complete city dataset. To explore real data, download a manageable CSV export from the City of San Francisco's [311 Cases dataset](https://data.sfgov.org/City-Infrastructure/311-Cases/vw6y-z8j6) and pass it with `--input`. No remote ingestion is required by this project.

## License

MIT. See [LICENSE](LICENSE).
