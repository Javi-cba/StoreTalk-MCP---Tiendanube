# Desarrollo local (backend)

Todos los comandos se corren desde `backend/`. Las variables se leen del `.env` del root del monorepo.

## Levantar el server

```bash
uv sync                                         # instalar dependencias
uv run alembic upgrade head                     # aplicar migraciones
uv run uvicorn src.main:app --reload            # API en :8000, MCP en :8000/mcp
```

Chequeo: http://localhost:8000/health → `{"status":"ok","db":"up"}`

> Si `uv` no se encuentra: `export PATH="$HOME/.local/bin:$PATH"`

## Conectar una tienda (OAuth Tiendanube)

El flujo arranca en el frontend con el usuario logueado en Clerk:

1. Entrar a http://localhost:3000/connect (pide login con Clerk).
2. "Conectar con Tiendanube" → `GET /api/tiendanube/install-url` (Bearer JWT de Clerk) → Tiendanube.
3. Tiendanube vuelve a `https://<tu-ngrok>/api/tiendanube/callback`, que redirige (303) a
   `http://localhost:3000/connect/callback?code=...&state=...`, que llama a
   `POST /api/tiendanube/connect` y muestra la tienda conectada y los scopes otorgados
   (se guardan en `connections.scopes`).

Redirect URL en el panel de Partners: `https://<tu-ngrok>/api/tiendanube/callback` (túnel al backend en :8000).
El backend reenvía `code`/`state` a `FRONTEND_ORIGIN/connect/callback` (http://localhost:3000). Si la Redirect URL
apunta a una ruta que no existe, Tiendanube vuelve igual y se ve un 404.

Clerk: el backend deriva issuer y JWKS de `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` (o `CLERK_PUBLISHABLE_KEY`)
del `.env`; tiene que ser la misma instancia que usa el frontend. `CLERK_ISSUER` / `CLERK_JWKS_URL`
lo pisan si hace falta.

## API keys de MCP (`stk_...`)

```bash
uv run python -m scripts.create_api_key <store_id> "nombre"    # crea una key nueva (se ve una sola vez)
uv run python -m scripts.show_store_token <store_id>           # token de Tiendanube descifrado (para Postman)
```

Solo funcionan con `ENVIRONMENT=development`.

## Conectar a Claude Code

```bash
claude mcp add --transport http --scope user storetalk http://localhost:8000/mcp \
  --header "Authorization: Bearer stk_..."
```

Dentro de `claude`, `/mcp` muestra el estado. Para quitarlo: `claude mcp remove storetalk`.

## Conectar a Claude Desktop (app)

Claude Desktop no acepta URL + header directo; se usa el puente `mcp-remote` (requiere Node/npx).
Editar `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "storetalk": {
      "command": "npx",
      "args": [
        "-y", "mcp-remote", "http://localhost:8000/mcp",
        "--allow-http",
        "--header", "Authorization:${STORETALK_AUTH}"
      ],
      "env": { "STORETALK_AUTH": "Bearer stk_..." }
    }
  }
}
```

Cerrar Claude Desktop por completo (Cmd+Q) y volver a abrirlo. El server aparece en el ícono de herramientas del chat.
Logs si no conecta: `~/Library/Logs/Claude/mcp-server-storetalk.log`.

## Probar tools a mano (MCP Inspector)

```bash
npx @modelcontextprotocol/inspector
```

Transport `Streamable HTTP` → URL `http://localhost:8000/mcp` → Bearer `stk_...` → Tools.

## Calidad

```bash
uv run pytest                              # todo
uv run pytest tests/test_mcp/products      # una entidad
uv run ruff check . && uv run ruff format .
uv run mypy src tests
```

Los tests de tools usan el harness de `tests/test_mcp/conftest.py` (sin DB ni Tiendanube reales):
`harness.call(tool, args)` / `harness.call_error(tool, args)`, `harness.set_scopes("read_products,...")`
para simular permisos faltantes, y `harness.audits` con lo que se hubiera escrito en `audit_log`.
Las respuestas de Tiendanube se mockean con `respx` sobre `BASE_URL`.

## Probar permisos (scopes) faltantes

Los scopes otorgados se guardan en `connections.scopes`. Para ver el error que recibe el usuario cuando
falta uno, quitá el scope de esa columna en la tienda de prueba (p. ej. dejar solo `read_products`) y
llamá una tool de escritura: responde con el scope literal que hay que agregar, sin desconectar la tienda.
La caché de API keys dura 60 s; el cambio de scopes se lee en cada llamada.

## Nueva migración

```bash
uv run alembic revision --autogenerate -m "descripcion"
uv run alembic upgrade head
```
