from typing import Annotated

from fastapi import APIRouter, Query

from app.api.deps import call_catalog, validate_period
from app.schemas.climate import Aggregation, ClimateVariable, Season

router = APIRouter()


@router.get("/climate/timeseries")
def climate_timeseries(
    variable: Annotated[ClimateVariable, Query()],
    start_year: Annotated[int, Query(ge=1981, le=2100)],
    end_year: Annotated[int, Query(ge=1981, le=2100)],
    aggregation: Annotated[Aggregation, Query()] = "annual",
    region_id: Annotated[str | None, Query()] = None,
    season: Annotated[Season | None, Query()] = None,
) -> dict:
    validate_period(start_year, end_year, aggregation, season)
    return call_catalog(
        "timeseries",
        variable=variable,
        start_year=start_year,
        end_year=end_year,
        aggregation=aggregation,
        season=season,
        region_id=region_id,
    )
