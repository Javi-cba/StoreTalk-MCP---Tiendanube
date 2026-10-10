# Frontend — Guía de estructura

Stack: **Next.js (App Router) + React + TypeScript + Tailwind CSS**. Landing page pública del producto + dashboard privado para que el comerciante conecte su tienda Tiendanube, genere API keys y configure el MCP en su cliente de IA (Claude, Cursor, etc.).

> Nombre comercial: TBD. No usar "Tiendanube" en el nombre del producto (riesgo de marca); sí en textos descriptivos ("conecta tu tienda Tiendanube").

## Librerías

- **tailwindcss** — estilos. Nada de CSS modules ni styled-components.
- **@clerk/nextjs** — login, **solo** para el área privada (dashboard). La landing es pública.
- **zod** — validación de datos que entran/salen de la API.
- **lucide-react** — íconos.
- **clsx + tailwind-merge** — composición de clases (`cn()` en `lib/utils/`).

## Estructura de carpetas

```
src/
├── app/                        # Rutas (App Router). Solo páginas y layouts.
│   ├── layout.tsx              # Layout raíz (fuentes, metadata). SIN ClerkProvider global.
│   ├── (marketing)/            # Landing pública, sin auth, SSG
│   │   ├── layout.tsx          # Navbar + Footer
│   │   └── page.tsx            # Home: hero, cómo funciona, tools, FAQ, CTA
│   └── (app)/                  # Área privada, protegida por Clerk
│       ├── layout.tsx          # ClerkProvider + sidebar del dashboard
│       ├── sign-in/[[...sign-in]]/page.tsx
│       ├── dashboard/page.tsx          # Tiendas conectadas + uso
│       ├── dashboard/api-keys/page.tsx # Crear / listar / revocar keys
│       └── connect/callback/page.tsx   # Vuelta del OAuth de Tiendanube (?code=...)
│
├── components/
│   ├── ui/                     # Primitivos genéricos: Button, Card, Badge, Modal...
│   ├── marketing/              # Secciones de la landing: Hero, HowItWorks, ToolsGrid, Faq, Cta
│   ├── dashboard/              # StoreCard, ApiKeyTable, UsageChart, McpConfigSnippet
│   └── layout/                 # Navbar, Footer, Sidebar
│
├── content/                    # ⭐ Copy de la landing como datos (tools, FAQ, pasos)
│   ├── tools.ts                # Lista de tools MCP que se muestran en la landing
│   └── faq.ts
│
├── lib/                        # ⭐ Lógica reutilizable, SIN JSX
│   ├── api/                    # Cliente HTTP hacia FastAPI
│   │   ├── client.ts           # fetch wrapper (base URL, Bearer token, ApiError)
│   │   ├── stores.ts           # getStores, getInstallUrl, connectStore, disconnectStore
│   │   ├── apiKeys.ts          # createApiKey, listApiKeys, revokeApiKey
│   │   └── usage.ts            # getUsage
│   ├── auth/                   # Config/helpers de Clerk
│   ├── mcp/                    # Generación de snippets de config MCP por cliente
│   ├── schemas/                # Schemas zod (tipos compartidos con la API)
│   └── utils/                  # cn(), formatos de fecha/número
│
├── hooks/                      # Custom hooks (useApiKeys, useStores...)
├── middleware.ts               # clerkMiddleware: protege solo /dashboard y /connect
└── types/                      # Tipos TypeScript globales
```

## Landing page

- Vive en el route group `(marketing)`: **estática (SSG), sin Clerk, sin llamadas al backend**. Rápida y buena para SEO.
- Cada sección es un componente en `components/marketing/`; `page.tsx` solo las compone en orden.
- El copy repetible (tools, FAQ, pasos) va en `content/` como arrays tipados, no hardcodeado en el JSX.
- Los CTA ("Conectar mi tienda") llevan a `/sign-in` → `/dashboard`.
- Metadata (title, description, Open Graph) con la Metadata API de Next en el layout/página.

## Autenticación (Clerk)

Clerk se usa **solo para quien quiere conectar su tienda y usar el MCP**. El visitante de la landing nunca pasa por Clerk.

- `ClerkProvider` envuelve solo el layout de `(app)`, no la raíz.
- `middleware.ts` usa `clerkMiddleware` + `createRouteMatcher` para proteger `/dashboard(.*)` y `/connect(.*)`. Todo lo demás es público.
- Clerk emite un **JWT** que se envía al backend en `Authorization: Bearer <token>`; FastAPI lo valida contra el JWKS.

## Flujo de conexión de tienda

1. En el dashboard, el usuario toca "Conectar tienda" → `GET /api/tiendanube/install-url` → redirect a Tiendanube.
2. Tiendanube vuelve a `/connect/callback?code=...`.
3. La página llama a `POST /api/tiendanube/connect` con el `code` y redirige a `/dashboard`.
4. El usuario genera una API key (se muestra **una sola vez**) y copia el snippet de config MCP (`lib/mcp/`) para su cliente de IA.

## Comunicación con el backend

El backend es **FastAPI** (ver `backend/README.md`). El front NO tiene backend propio: nada de Route Handlers ni Server Actions como proxy.

- **Toda llamada pasa por `lib/api/`**, nunca `fetch` suelto en un componente.
- **Client Components** → token con `useAuth().getToken()`, se pasa a `lib/api/`.
- **Server Components** → token con `auth()` de `@clerk/nextjs/server`.
- El `user_id` lo deriva SIEMPRE el backend del JWT; el front nunca lo manda.
- `lib/api/client.ts` parsea el error estándar `{ error: { code, message } }` y lanza `ApiError(code, message, status)`; el `message` viene en español, listo para mostrar.
- Las respuestas se validan con zod (`lib/schemas/`) antes de usarse.

## Variables de entorno (`.env.example`)

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=
CLERK_SECRET_KEY=
NEXT_PUBLIC_CLERK_SIGN_IN_URL=/sign-in
NEXT_PUBLIC_CLERK_SIGN_IN_FALLBACK_REDIRECT_URL=/dashboard
NEXT_PUBLIC_MCP_URL=http://localhost:8000/mcp
```

## Reglas

- **`app/` solo orquesta.** Las páginas importan de `components/`, `lib/` y `content/`; sin lógica pesada.
- **`lib/` = todo lo reutilizable y sin UI.** Nunca JSX en `lib/`.
- **La landing no depende de Clerk ni del backend.** Si una sección necesita datos, salen de `content/`.
- **Server Components por defecto.** `"use client"` solo donde hay interactividad (forms, copiar al portapapeles, modales).
- **Toda llamada al backend pasa por `lib/api/`** y va directo a FastAPI.
- **Tipos compartidos con la API en `lib/schemas/` (zod)**, derivados con `z.infer`.
- **Nunca loguear ni persistir API keys** en el cliente (ni `localStorage`). Se muestran una vez y listo.
- **Tailwind para todo el estilo**; variantes de componentes con `cn()`, sin clases inline gigantes repetidas.
