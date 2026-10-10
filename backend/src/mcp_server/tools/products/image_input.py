"""Image input accepted by the product tools, validated before reaching Tiendanube.

Tiendanube accepts a public URL (`src`) or base64 (`attachment` + `filename`);
formats .gif/.jpg/.png/.webp, < 10MB.
Docs: https://tiendanube.github.io/api-documentation/resources/product-image
"""

import base64
import binascii
import re
from pathlib import PurePosixPath
from typing import Annotated, Any, Self
from urllib.parse import urlparse

from fastmcp.exceptions import ToolError
from pydantic import BaseModel, Field, model_validator

from src.services.tiendanube.resources.images import ALLOWED_FORMATS, MAX_IMAGE_BYTES

_DATA_URI = re.compile(r"^data:image/[\w.+-]+;base64,", re.IGNORECASE)
_URL_EXTENSIONS = {"jpg", "jpeg", "png", "gif", "webp"}
_UNSUPPORTED_MESSAGE = (
    "Tiendanube solo acepta imágenes JPG, PNG, GIF o WEBP de menos de 10MB. "
    "Convertí la imagen a uno de esos formatos y volvé a intentar."
)


class ImageInput(BaseModel):
    url: Annotated[
        str | None, Field(description="Public http(s) URL of the image (preferred).")
    ] = None
    base64: Annotated[
        str | None,
        Field(description="Image content in base64 (a 'data:image/...;base64,' prefix is OK)."),
    ] = None
    filename: Annotated[str | None, Field(description="Original file name (only with base64).")] = (
        None
    )
    position: Annotated[int | None, Field(ge=1, description="1 = main image.")] = None
    alt: Annotated[str | None, Field(max_length=255, description="Alt text (SEO).")] = None

    @model_validator(mode="after")
    def _one_source(self) -> Self:
        if bool(self.url) == bool(self.base64):
            raise ValueError("Each image needs exactly one of `url` or `base64`.")
        return self


def detect_format(data: bytes) -> str | None:
    """Real format from magic bytes (the extension of a file name can lie)."""
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if data.startswith(b"\xff\xd8\xff"):
        return "jpg"
    if data[:6] in (b"GIF87a", b"GIF89a"):
        return "gif"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "webp"
    return None


def to_payload(image: ImageInput, language: str | None) -> dict[str, Any]:
    """Build the POST /products/{id}/images body. Raises ToolError on invalid images."""
    payload: dict[str, Any] = {}
    if image.url:
        parsed = urlparse(image.url)
        if parsed.scheme not in ("http", "https") or not parsed.netloc:
            raise ToolError(f"La URL de imagen no es válida: {image.url}")
        extension = PurePosixPath(parsed.path).suffix.lower().lstrip(".")
        if extension and extension not in _URL_EXTENSIONS and len(extension) <= 4:
            raise ToolError(f"Formato .{extension} no soportado. {_UNSUPPORTED_MESSAGE}")
        payload["src"] = image.url
    else:
        assert image.base64 is not None
        raw = _DATA_URI.sub("", image.base64.strip())
        try:
            data = base64.b64decode(raw, validate=False)
        except (binascii.Error, ValueError) as exc:
            raise ToolError("El contenido base64 de la imagen no es válido.") from exc
        if len(data) > MAX_IMAGE_BYTES:
            raise ToolError(f"La imagen pesa más de 10MB. {_UNSUPPORTED_MESSAGE}")
        fmt = detect_format(data)
        if fmt not in ALLOWED_FORMATS:
            raise ToolError(_UNSUPPORTED_MESSAGE)
        stem = PurePosixPath(image.filename or "imagen").stem or "imagen"
        payload["attachment"] = base64.b64encode(data).decode()
        payload["filename"] = f"{stem}.{fmt}"
    if image.position is not None:
        payload["position"] = image.position
    if image.alt:
        payload["alt"] = {(language or "es"): image.alt}
    return payload
