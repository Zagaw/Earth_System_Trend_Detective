from typing import Literal

from pydantic import BaseModel, Field


ClimateVariable = Literal["precipitation", "temperature", "relative_humidity"]
Aggregation = Literal["monthly", "annual", "seasonal"]
Season = Literal["DJF", "MAM", "JJA", "SON", "monsoon"]


class TimeSeriesQuery(BaseModel):
    variable: ClimateVariable
    start_year: int = Field(ge=1981, le=2100)
    end_year: int = Field(ge=1981, le=2100)
    aggregation: Aggregation = "annual"
    region_id: str | None = None
    season: Season | None = None
