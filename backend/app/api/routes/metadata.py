from dataclasses import asdict

from fastapi import APIRouter

from app.core.config import get_settings
from app.core.variables import FILL_VALUE, REGIONAL_MINIMUM_SPAN_DEGREES, VARIABLES
from app.schemas.common import (
    AnalysisConfigResponse,
    MetadataResponse,
    Period,
    VariableInfo,
    VerificationSample,
)
from app.services.catalog import CatalogNotReady, get_catalog

router = APIRouter()


@router.get("/metadata", response_model=MetadataResponse)
def metadata() -> MetadataResponse:
    settings = get_settings()
    return MetadataResponse(
        project="EarthTrend Myanmar",
        geography="Myanmar",
        community=settings.nasa_power_community,
        nasa_power_base_url=settings.nasa_power_base_url,
        requested_period=Period(
            start_year=settings.default_start_year,
            end_year=settings.default_end_year,
        ),
        study_grid_status=_coverage().get("study_grid_status", "not_ingested"),
        fill_value=FILL_VALUE,
        month_key_policy=(
            "YYYYMM keys with months 01–12 are monthly observations. "
            "Month code 13 is an API annual summary and is stored separately. "
            "It is not a month and, for precipitation, it is not an accumulated annual total."
        ),
        regional_minimum_span_degrees=REGIONAL_MINIMUM_SPAN_DEGREES,
        grid_note=(
            "A 2° by 2° regional sample used the MERRA-2 native grid: "
            "0.5° latitude and 0.625° longitude. The third point coordinate "
            "is stored as elevation in metres because the sample values follow terrain, "
            "but it is not used in calculations yet."
        ),
        variables=[VariableInfo.model_validate(asdict(item)) for item in VARIABLES.values()],
        verification=[
            VerificationSample(
                retrieved_on="2026-10-09",
                description=(
                    "Point request at 16.8°N, 96.1°E for 2020 and for 2024–2025. "
                    "Communities SB, AG, and RE returned the same units and the same "
                    "2024–2025 values for T2M, PRECTOTCORR, and RH2M."
                ),
                community="SB, AG, RE",
                parameters=["T2M", "PRECTOTCORR", "RH2M"],
                coverage_note=(
                    "That single point returned months through December 2025. "
                    "This does not establish complete 2001–2025 coverage for every "
                    "Myanmar grid cell."
                ),
            ),
            VerificationSample(
                retrieved_on="2026-10-09",
                description=(
                    "Regional request, community SB, latitude 16–18, longitude 96–98, "
                    "parameter T2M, year 2020. The response was a FeatureCollection of 15 points."
                ),
                community="SB",
                parameters=["T2M"],
                coverage_note="Parser fixture: backend/tests/fixtures/power_regional_t2m_2020.json.",
            ),
        ],
        incomplete=_coverage()["limitations"],
    )


@router.get("/analysis/config", response_model=AnalysisConfigResponse)
def analysis_config() -> AnalysisConfigResponse:
    settings = get_settings()
    return AnalysisConfigResponse(
        significance_alpha=settings.significance_alpha,
        trend_method="sen_slope",
        significance_test="mann_kendall_on_annual_or_seasonal_series",
        autocorrelation_method="not_selected",
        multiple_testing="benjamini_hochberg",
        minimum_valid_years=settings.minimum_valid_years,
        minimum_valid_months_for_means=settings.minimum_valid_months_for_means,
        minimum_valid_months_for_rainfall_total=settings.minimum_valid_months_for_rainfall_total,
        trend_statuses=[
            "significant_increasing",
            "significant_decreasing",
            "not_significant",
            "insufficient_data",
        ],
        seasons_planned=["DJF", "MAM", "JJA", "SON", "monsoon"],
        calculations_implemented=True,
        note=(
            "Sen's slope and Mann–Kendall run on annual or seasonal series. "
            "Lag-1 autocorrelation is measured on the Sen residuals; Hamed–Rao "
            "correction is used when its absolute value is at least 0.3. "
            "Grid and state/region p-values are adjusted with Benjamini–Hochberg. "
            "The Myanmar monsoon season is May–October."
        ),
    )


def _coverage() -> dict:
    try:
        catalog = get_catalog()
    except CatalogNotReady:
        return {
            "study_grid_status": "not_ingested",
            "limitations": [
                "The Myanmar study grid has not been ingested yet. Run python -m app.cli ingest.",
            ],
        }
    info = catalog.metadata()
    return {
        "study_grid_status": "ready",
        "limitations": [
            (
                f"Masked cells: {info['masked_cell_count']}. "
                f"Observed months {info['actual_start_year']}–{info['actual_end_year']}. "
                f"Cells on an ADM1 boundary assigned to the first match: {info['boundary_overlap_cells']}. "
                f"Interior cells without an ADM1 match: {info['unassigned_interior_cells']}."
            ),
            "Elevation is stored and is not used in the trend calculations.",
            "No crop, health, flood, or economic outcome dataset is included.",
        ],
    }
