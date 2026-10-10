"""Tiendanube HTTP errors mapped to messages readable by the LLM / end user."""


class TiendanubeError(Exception):
    code = "tiendanube_error"

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class TiendanubeAuthError(TiendanubeError):
    code = "store_disconnected"


class TiendanubeNotFoundError(TiendanubeError):
    code = "not_found"


class TiendanubeValidationError(TiendanubeError):
    code = "validation_error"


class TiendanubeRateLimitError(TiendanubeError):
    code = "rate_limited"


class TiendanubePaymentRequiredError(TiendanubeError):
    code = "payment_required"


class TiendanubeUnavailableError(TiendanubeError):
    code = "unavailable"
