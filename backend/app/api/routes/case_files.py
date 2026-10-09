from typing import Annotated

from fastapi import APIRouter, Query

from app.api.deps import call_catalog, validate_period

router = APIRouter()


@router.get("/case-files")
def case_files(
    start_year: Annotated[int, Query(ge=1981, le=2100)] = 2001,
    end_year: Annotated[int, Query(ge=1981, le=2100)] = 2025,
) -> dict:
    validate_period(start_year, end_year, "annual", None)
    return call_catalog("case_file", start_year=start_year, end_year=end_year)
