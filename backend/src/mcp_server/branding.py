"""StoreTalk icon for MCP clients.

It travels inside `serverInfo.icons` as a data URI (MCP spec: Implementation.icons), so it works
even on localhost / ngrok without a public static URL. The same file is served as the favicon,
which is where clients that add the server by URL (Connectors) take the icon from.
"""

import base64
from functools import cache
from pathlib import Path

from mcp.types import Icon

ICON_PATH = Path(__file__).parent / "assets" / "icon.png"  # 128x128, app icon from the frontend


@cache
def icon_bytes() -> bytes:
    return ICON_PATH.read_bytes()


def server_icons() -> list[Icon]:
    data = base64.b64encode(icon_bytes()).decode()
    return [Icon(src=f"data:image/png;base64,{data}", mime_type="image/png", sizes=["128x128"])]
