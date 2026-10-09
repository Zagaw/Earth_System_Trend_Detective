class AppError(Exception):
    def __init__(self, status_code: int, error: str, message: str) -> None:
        self.status_code = status_code
        self.error = error
        self.message = message
        super().__init__(message)


class PowerClientError(Exception):
    def __init__(self, message: str, status_code: int | None = None) -> None:
        self.status_code = status_code
        super().__init__(message)


class NormalizationError(ValueError):
    pass


def not_ready(capability: str) -> None:
    raise AppError(
        status_code=503,
        error="not_ready",
        message=(
            f"{capability} is not available yet. NASA POWER parameter metadata "
            "has been verified, but the Myanmar study grid has not been ingested "
            "or analyzed."
        ),
    )
