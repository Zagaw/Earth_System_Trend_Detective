from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    app_name: str = "EarthTrend Myanmar API"
    app_version: str = "0.1.0"
    api_prefix: str = "/api/v1"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    nasa_power_base_url: str = "https://power.larc.nasa.gov/api"
    nasa_power_community: str = "SB"
    nasa_timeout_seconds: float = 120
    nasa_max_retries: int = 3

    default_start_year: int = 2001
    default_end_year: int = 2025
    latitude_min: float = 9
    latitude_max: float = 29
    longitude_min: float = 92
    longitude_max: float = 102

    data_dir: Path = Path("./data")
    cache_enabled: bool = True
    cache_ttl_seconds: int = 86400
    processing_version: str = "0.1.0"

    understand_ai_api_key: str = ""
    understand_ai_base_url: str = "https://openrouter.ai/api/v1"
    understand_ai_model: str = "nvidia/nemotron-3-ultra-550b-a55b:free"
    understand_ai_timeout_seconds: float = 90

    significance_alpha: float = 0.05
    minimum_valid_years: int = 10
    minimum_valid_months_for_means: int = 10
    minimum_valid_months_for_rainfall_total: int = 12
    minimum_spatial_coverage: float = 0.5

    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).resolve().parents[2] / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def raw_dir(self) -> Path:
        return self.data_dir / "raw"

    @property
    def processed_dir(self) -> Path:
        return self.data_dir / "processed"

    @property
    def cache_dir(self) -> Path:
        return self.data_dir / "cache"

    @property
    def boundary_dir(self) -> Path:
        return self.data_dir / "boundaries"


@lru_cache
def get_settings() -> Settings:
    return Settings()
