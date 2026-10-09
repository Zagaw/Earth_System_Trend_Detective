from app.core.errors import AppError
from app.schemas.climate import Aggregation, Season
from app.services.catalog import CatalogNotReady, UnknownRegion, get_catalog


def reject_monthly_trends(aggregation: Aggregation) -> None:
    if aggregation == "monthly":
        raise AppError(
            status_code=422,
            error="invalid_aggregation",
            message="Trend tests use annual or seasonal series. Raw monthly values are not tested.",
        )


def validate_period(
    start_year: int,
    end_year: int,
    aggregation: Aggregation,
    season: Season | None,
) -> None:
    if end_year < start_year:
        raise AppError(
            status_code=422,
            error="invalid_period",
            message="end_year must be greater than or equal to start_year.",
        )
    if aggregation == "seasonal" and season is None:
        raise AppError(
            status_code=422,
            error="invalid_season",
            message=(
                "A season is required when aggregation is seasonal. "
                "Use DJF, MAM, JJA, SON, or monsoon."
            ),
        )


def load_catalog():
    try:
        return get_catalog()
    except CatalogNotReady as exc:
        raise AppError(status_code=503, error="not_ready", message=str(exc)) from exc


def call_catalog(method_name: str, /, **kwargs):
    catalog = load_catalog()
    try:
        return getattr(catalog, method_name)(**kwargs)
    except UnknownRegion as exc:
        raise AppError(
            status_code=404,
            error="unknown_region",
            message=f"No region is registered with id {exc}.",
        ) from exc
    except ValueError as exc:
        raise AppError(status_code=422, error="invalid_request", message=str(exc)) from exc
