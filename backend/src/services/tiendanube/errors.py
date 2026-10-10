"""Tiendanube HTTP errors mapped to messages readable by the LLM / end user."""

from src.services.tiendanube.scopes import Scope, missing_scope_message


class TiendanubeError(Exception):
    code = "tiendanube_error"

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class TiendanubeAuthError(TiendanubeError):
    """The access token is invalid (app uninstalled). The connection must be revoked."""

    code = "store_disconnected"


class TiendanubeMissingScopeError(TiendanubeError):
    """The token is valid but was not granted the scope this call needs. Never revoke."""

    code = "missing_scope"

    def __init__(self, scope: Scope) -> None:
        super().__init__(missing_scope_message(scope))
        self.scope = scope


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
