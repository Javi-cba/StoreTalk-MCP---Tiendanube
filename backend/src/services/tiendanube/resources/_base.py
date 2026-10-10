from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.services.tiendanube.client import TiendanubeClient


class Resource:
    def __init__(self, client: "TiendanubeClient") -> None:
        self._client = client
