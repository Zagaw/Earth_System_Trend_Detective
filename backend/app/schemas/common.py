from typing import Literal

from pydantic import BaseModel, Field


class ApiError(BaseModel):
    error: str
    message: str


class HealthResponse(BaseModel):
    status: Literal["ok"]
    service: str
    version: str


class Period(BaseModel):
    start_year: int
    end_year: int


class VariableInfo(BaseModel):
    id: Literal["precipitation", "temperature", "relative_humidity"]
    label: str
    source_parameter: str
    source_unit: str
    long_name: str
    temporal_meaning: str
    analysis_unit: str
    aggregation_rule: str
    slope_unit: str
    conversion: str | None = None
    verified: bool
    verified_on: str


class VerificationSample(BaseModel):
    retrieved_on: str
    description: str
    community: str
    parameters: list[str]
    coverage_note: str


class MetadataResponse(BaseModel):
    project: str
    geography: str
    community: str
    nasa_power_base_url: str
    requested_period: Period
    study_grid_status: Literal["not_ingested", "ready"]
    fill_value: float
    month_key_policy: str
    regional_minimum_span_degrees: float
    grid_note: str
    variables: list[VariableInfo]
    verification: list[VerificationSample]
    incomplete: list[str]


class AnalysisConfigResponse(BaseModel):
    significance_alpha: float
    trend_method: str
    significance_test: str
    autocorrelation_method: str
    multiple_testing: str
    minimum_valid_years: int = Field(ge=1)
    minimum_valid_months_for_means: int
    minimum_valid_months_for_rainfall_total: int
    trend_statuses: list[str]
    seasons_planned: list[str]
    calculations_implemented: bool
    note: str
