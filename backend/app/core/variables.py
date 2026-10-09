from dataclasses import dataclass


@dataclass(frozen=True)
class VariableDefinition:
    id: str
    label: str
    source_parameter: str
    source_unit: str
    long_name: str
    temporal_meaning: str
    analysis_unit: str
    aggregation_rule: str
    slope_unit: str
    conversion: str | None
    verified: bool
    verified_on: str


# Units and names were read from live NASA POWER responses on 2026-10-09.
# See docs/data-dictionary.md. Do not change them without a new verification.
VARIABLES: dict[str, VariableDefinition] = {
    "precipitation": VariableDefinition(
        id="precipitation",
        label="Rainfall",
        source_parameter="PRECTOTCORR",
        source_unit="mm/day",
        long_name="Precipitation Corrected",
        temporal_meaning=(
            "Monthly value is a mean daily precipitation rate, not an accumulated "
            "monthly total. The API also returns an annual summary under month code 13."
        ),
        analysis_unit="mm",
        aggregation_rule=(
            "Monthly accumulation = daily rate × days in that month. "
            "Annual rainfall is the sum of valid monthly accumulations. "
            "Do not use the API month-13 value as an annual total."
        ),
        slope_unit="mm/year",
        conversion="monthly_mm = mm_per_day * days_in_month",
        verified=True,
        verified_on="2026-10-09",
    ),
    "temperature": VariableDefinition(
        id="temperature",
        label="Air temperature at 2 m",
        source_parameter="T2M",
        source_unit="C",
        long_name="Temperature at 2 Meters",
        temporal_meaning=(
            "Monthly mean air temperature. The source unit is degrees Celsius, "
            "so no Kelvin conversion is applied. Month code 13 is an annual summary, "
            "not a month."
        ),
        analysis_unit="degC",
        aggregation_rule="Annual and seasonal values are means of valid monthly values, not sums.",
        slope_unit="degC/year",
        conversion=None,
        verified=True,
        verified_on="2026-10-09",
    ),
    "relative_humidity": VariableDefinition(
        id="relative_humidity",
        label="Relative humidity at 2 m",
        source_parameter="RH2M",
        source_unit="%",
        long_name="Relative Humidity at 2 Meters",
        temporal_meaning=(
            "Monthly mean relative humidity in percent. Month code 13 is an annual "
            "summary, not a month."
        ),
        analysis_unit="%",
        aggregation_rule=(
            "Annual and seasonal values are means of valid monthly values. "
            "Trend slopes are percentage points per year."
        ),
        slope_unit="percentage_points/year",
        conversion=None,
        verified=True,
        verified_on="2026-10-09",
    ),
}

VARIABLE_IDS = tuple(VARIABLES)
SOURCE_PARAMETERS = {item.source_parameter: item for item in VARIABLES.values()}
FILL_VALUE = -999.0
REGIONAL_MINIMUM_SPAN_DEGREES = 2.0
