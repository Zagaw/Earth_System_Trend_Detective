# Data dictionary

Verification date: 2026-10-09. Values below come from live NASA POWER responses, not from assumed units.

## Study area

- Geography: Myanmar.
- Requested analysis period: 2001–2025.
- Initial request bounds: latitude 9–29, longitude 92–102. This is a request window, not the administrative boundary.
- National grid status: ingested on 2026-10-09.
- The regional API accepts at most a 10 degree latitude or longitude span, so the study window is requested as two tiles: latitude 9–19 and 19.01–29, both with longitude 92–102.
- The merged grid has 656 MERRA-2 cells. 190 cell centres fall inside the Myanmar boundary and are used in the analysis.
- Monthly values are present from January 2001 through December 2025 in that masked grid. That is the actual stored coverage, not an assumption that every scientific use of the latest year is complete.

## NASA POWER

- Base URL: `https://power.larc.nasa.gov/api`
- Service: POWER Monthly and Annual API, observed version `v2.10.0` on the point request.
- Default community: `SB`. The same point request with communities `AG` and `RE` returned the same units and the same 2024–2025 values for all three parameters.
- Missing-value sentinel: `-999`. Parsed values equal to the sentinel become missing. Zero is a valid observation.
- Time keys: `YYYYMM`. Months `01`–`12` are monthly observations. Month `13` is an API annual summary. It is stored separately and is not used as a month.
- Time standard reported by the API: `LST`.
- Regional requests must span at least 2 degrees of latitude and 2 degrees of longitude. Smaller areas must use the point endpoint.

### Precipitation

| Field | Value |
|---|---|
| Internal name | `precipitation` |
| Parameter | `PRECTOTCORR` |
| API long name | Precipitation Corrected |
| Source unit | `mm/day` |
| Temporal meaning | Mean daily precipitation rate for the month |
| Analysis unit | `mm` |
| Conversion | `monthly_mm = mm_per_day × days_in_month` |
| Annual rule | Sum of valid monthly accumulations |
| Slope unit | `mm/year` |

The 2020 point sample's month-13 value was the rounded mean of the twelve monthly rates, not an accumulated annual total. Do not use month 13 as annual rainfall.

### Air temperature

| Field | Value |
|---|---|
| Internal name | `temperature` |
| Parameter | `T2M` |
| API long name | Temperature at 2 Meters |
| Source unit | `C` |
| Temporal meaning | Monthly mean |
| Analysis unit | `degC` |
| Conversion | None. The source is already degrees Celsius. |
| Annual rule | Mean of valid monthly values |
| Slope unit | `degC/year` |

### Relative humidity

| Field | Value |
|---|---|
| Internal name | `relative_humidity` |
| Parameter | `RH2M` |
| API long name | Relative Humidity at 2 Meters |
| Source unit | `%` |
| Temporal meaning | Monthly mean |
| Analysis unit | `%` |
| Conversion | None |
| Annual rule | Mean of valid monthly values |
| Slope unit | percentage points per year |

## Samples used for verification

1. Point `16.8°N, 96.1°E`, year 2020, and years 2024–2025. December 2025 was present for all three parameters at this single point.
2. Regional community `SB`, latitude 16–18, longitude 96–98, `T2M`, year 2020. Fifteen point features. Saved at `backend/tests/fixtures/power_regional_t2m_2020.json`.

That regional sample used coordinates spaced by 0.5° latitude and 0.625° longitude, matching MERRA-2 native resolution. The third coordinate behaved like elevation in metres (about 0.06 m near 16°N and about 480 m at 18°N, 97.5°E). It is stored as `elevation_m` and is not used in calculations yet.

## Not established by these samples

- Complete 2001–2025 coverage for every cell in the Myanmar request window.
- The masking rule that will decide which cells belong to Myanmar.
- Cell assignment to states and regions.
- Any trend, anomaly, or impact number.
