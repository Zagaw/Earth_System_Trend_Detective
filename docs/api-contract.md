# API contract

Prefix: `/api/v1`

Interactive docs in development: `http://127.0.0.1:8000/docs`

## Available now

- `GET /health` — service status.
- `GET /metadata` — verified variables, units, fill value, and current data limitations.
- `GET /analysis/config` — chosen statistical settings. `calculations_implemented` is `true`.

## Analysis routes

After `python -m app.cli ingest`, these routes return calculated NASA POWER results. Before that file exists they return HTTP 503 with `error: not_ready`.

Monthly aggregation is accepted for time series and rejected for trend tests.

## Previous not-ready contract

Before ingestion, the same routes validate query parameters and return HTTP 503:

```json
{
  "error": "not_ready",
  "message": "..."
}
```

- `GET /climate/timeseries`
- `GET /trends/summary`
- `GET /trends/grid`
- `GET /trends/region`
- `GET /regions`
- `GET /regions/{region_id}/summary`
- `GET /compare`
- `GET /impact/summary`
- `GET /impact/anomalies`
- `GET /export/timeseries.csv`
- `GET /export/trends.csv`
- `GET /export/trends.geojson`
- `GET /export/impact.csv`

They do not return example climate values.

## Validation

- `variable`: `precipitation`, `temperature`, or `relative_humidity`.
- `aggregation`: `monthly`, `annual`, or `seasonal`.
- `season`, when aggregation is `seasonal`: `DJF`, `MAM`, `JJA`, or `SON`.
- `start_year` and `end_year`: integers from 1981 through 2100, with `end_year` greater than or equal to `start_year`.
- Unknown variables and a reversed period return HTTP 422.

## Time series shape

When ingestion exists, annual temperature responses will use this shape. The numbers are not filled in until then.

```json
{
  "variable": "temperature",
  "unit": "degC",
  "aggregation": "annual",
  "region_id": null,
  "start_year": 2001,
  "end_year": 2025,
  "source": "NASA POWER",
  "data": []
}
```
