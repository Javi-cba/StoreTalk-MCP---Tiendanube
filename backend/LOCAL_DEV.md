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

Con el admin de la tienda de prueba abierto, entrar a:

http://localhost:8000/api/tiendanube/install

Al aceptar los permisos se muestra un JSON con la `api_key` (una sola vez).
Redirect URL en el panel de Partners: `http://localhost:8000/api/tiendanube/callback`.

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
uv run pytest
uv run ruff check . && uv run ruff format .
uv run mypy src
```

## Nueva migración

```bash
uv run alembic revision --autogenerate -m "descripcion"
uv run alembic upgrade head
```
