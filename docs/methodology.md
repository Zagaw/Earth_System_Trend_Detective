# Methodology

This page records the rules chosen for EarthTrend Myanmar. Calculations that are not implemented yet are marked as such. The application does not display climate results until those functions run on ingested NASA POWER data.

## Aggregations

- Precipitation monthly values are mean daily rates in `mm/day`. A monthly total is `rate × days in the month`, using the calendar length of that month. An annual total is the sum of those monthly totals.
- A rainfall year is complete only when all 12 months are valid. A partial year is not treated as a full annual total.
- Temperature and relative humidity annual values are means of valid months. The default completeness rule is at least 10 of 12 months. This threshold is a policy choice.
- The API month-13 summary is not an input to these aggregations.
- Planned seasons are the meteorological seasons DJF, MAM, JJA, and SON. A monsoon definition is not selected yet. Seasonal aggregation is not calculated yet.

## Trend rules

These settings are exposed by `GET /api/v1/analysis/config`. The calculations themselves are not implemented.

- Magnitude: Sen's slope on the annual or seasonal series.
- Test: Mann–Kendall, or a seasonal variant when the series is seasonal. Ordinary Mann–Kendall will not be applied to raw monthly values.
- Significance level: 0.05.
- Grid maps: Benjamini–Hochberg false discovery rate across the family of valid cells for one variable and period.
- Statuses: `significant_increasing`, `significant_decreasing`, `not_significant`, `insufficient_data`.
- Minimum annual observations before a standard trend classification: 10.
- Autocorrelation correction: not selected yet.
- A non-significant result means the test did not meet the threshold. It is not evidence that the climate is unchanged.

## Boundaries

- National boundary: geoBoundaries gbOpen Myanmar ADM0, retrieved 2026-10-09, boundary year 2021, source OpenStreetMap, licence CC BY-SA 2.0. Shape ID `35516675B14551075264028`.
- States and regions: geoBoundaries gbOpen Myanmar ADM1, retrieved 2026-10-09, boundary year 2019, source Myanmar Analytics Project, licence CC BY 4.0. Stable IDs are the geoBoundaries `shapeID` values.
- A cell is included when its centre is covered by the national polygon. State assignment uses the same centre test. No cell in this grid matched more than one state, and every interior cell matched a state.
- Regional values are area-weighted means of cell values, with weights proportional to cos(latitude). A regional year is kept when valid cells cover at least half of the region's weight.

## What the app will not claim

Trend and anomaly results describe the climate series. They do not, by themselves, measure crop loss, health impacts, flood damage, or economic cost.
