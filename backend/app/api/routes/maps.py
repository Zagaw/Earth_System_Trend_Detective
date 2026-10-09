from typing import Annotated

from fastapi import APIRouter, Query

from app.api.deps import call_catalog, reject_monthly_trends, validate_period
from app.schemas.climate import Aggregation, ClimateVariable, Season

router = APIRouter()


@router.get("/regions")
def regions() -> dict:
    return {"regions": call_catalog("list_regions")}


@router.get("/regions/{region_id}/summary")
def region_summary(
    region_id: str,
    variable: Annotated[ClimateVariable, Query()] = "temperature",
    start_year: Annotated[int, Query(ge=1981, le=2100)] = 2001,
    end_year: Annotated[int, Query(ge=1981, le=2100)] = 2025,
    aggregation: Annotated[Aggregation, Query()] = "annual",
    season: Annotated[Season | None, Query()] = None,
) -> dict:
    validate_period(start_year, end_year, aggregation, season)
    reject_monthly_trends(aggregation)
    return call_catalog(
        "trend",
        variable=variable,
        start_year=start_year,
        end_year=end_year,
        aggregation=aggregation,
        season=season,
        region_id=region_id,
    )


@router.get("/compare")
def compare(
    variable: Annotated[ClimateVariable, Query()],
    start_year: Annotated[int, Query(ge=1981, le=2100)],
    end_year: Annotated[int, Query(ge=1981, le=2100)],
    region_id: Annotated[list[str], Query(min_length=2)],
    aggregation: Annotated[Aggregation, Query()] = "annual",
    season: Annotated[Season | None, Query()] = None,
) -> dict:
    validate_period(start_year, end_year, aggregation, season)
    reject_monthly_trends(aggregation)
    return call_catalog(
        "compare",
        variable=variable,
        start_year=start_year,
        end_year=end_year,
        aggregation=aggregation,
        season=season,
        region_ids=region_id,
    )
