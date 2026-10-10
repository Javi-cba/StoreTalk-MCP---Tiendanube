# Frontend — Guía de estructura

Stack: **Next.js (App Router) + React + TypeScript + Tailwind CSS**. Landing page pública del producto + dashboard privado para que el comerciante conecte su tienda Tiendanube, genere API keys y configure el MCP en su cliente de IA (Claude, Cursor, etc.).

> Nombre comercial: TBD. No usar "Tiendanube" en el nombre del producto (riesgo de marca); sí en textos descriptivos ("conecta tu tienda Tiendanube").

## Librerías

- **tailwindcss** — estilos. Nada de CSS modules ni styled-components.
- **@clerk/nextjs** — login, **solo** para el área privada (dashboard). La landing es pública.
- **zod** — validación de datos que entran/salen de la API.
- **lucide-react** — íconos. Los que no existen en lucide (logos de marca como Tiendanube) van como componentes SVG en `components/ui/icons/`, con `fill="currentColor"` y prop `size`.
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
├── components/                 # Ver "Componentes: organización y reutilización"
│   ├── ui/                     # Primitivos genéricos, sin lógica de negocio
│   │   ├── button/             #   Button.tsx (+ variantes)
│   │   ├── card/
│   │   ├── modal/              #   ConfirmDialog (<dialog> nativo; tone="danger" para acciones destructivas)
│   │   └── icons/              #   SVG propios como componentes (TiendanubeIcon...); el resto, lucide-react
│   ├── layout/                 # Navbar, Footer, Sidebar
│   ├── marketing/              # Secciones de la landing, una carpeta por sección
│   │   ├── hero/
│   │   ├── how-it-works/
│   │   ├── tools-grid/         #   ToolsGrid.tsx + ToolCard.tsx (subcomponente local)
│   │   └── faq/
│   └── dashboard/              # Una carpeta por dominio
│       ├── stores/             #   StoreCard, StoreList, ConnectStoreButton
│       ├── api-keys/           #   ApiKeyTable, CreateApiKeyModal
│       ├── usage/              #   UsageChart
│       └── mcp-config/         #   McpConfigSnippet
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
├── proxy.ts                    # clerkMiddleware: protege /dashboard(.*) y /connect (no /connect/callback)
└── types/                      # Tipos TypeScript globales
```

## Componentes: organización y reutilización

El objetivo es que `components/` escale sin convertirse en una carpeta plana con decenas de archivos mezclados.

**Dónde va cada componente**

| Tipo | Carpeta | Regla |
|------|---------|-------|
| Primitivo genérico (Button, Input, Card, Modal, Badge) | `components/ui/` | No conoce el dominio, no llama a la API, solo recibe props. |
| Estructura de página (Navbar, Footer, Sidebar) | `components/layout/` | Compartido entre layouts. |
| Sección de la landing | `components/marketing/<seccion>/` | Una carpeta por sección. |
| Componente de un dominio del dashboard | `components/dashboard/<dominio>/` | Una carpeta por dominio (`stores`, `api-keys`, `usage`...). |

**Reglas**

- **Una carpeta por componente o por dominio, nunca archivos sueltos** directamente en `components/marketing/` o `components/dashboard/`.
- **Máximo ~8 archivos por carpeta.** Si se pasa, se divide en subcarpetas por responsabilidad.
- **Un componente por archivo**, nombre en `PascalCase.tsx` igual al del componente; carpetas en `kebab-case`.
- **Subcomponentes locales al lado de su padre** (ej. `ToolCard` dentro de `tools-grid/`). No se exportan fuera de su carpeta.
- **Regla de promoción:** si un componente se usa en **2 o más dominios/secciones**, se generaliza (props en vez de datos del dominio) y se mueve a `components/ui/`. Nunca se importa un componente de `dashboard/stores/` desde `dashboard/api-keys/`.
- **Antes de crear un componente, buscar en `components/ui/`.** No duplicar botones, cards o modales con estilos propios; extender el primitivo con variantes (`cn()` + prop `variant`/`size`).
- **Dirección de imports:** `app/` → `components/<dominio>` → `components/ui` → `lib/`. Nunca al revés (`ui/` no importa de `dashboard/` ni de `marketing/`).
- **Sin lógica de datos en `ui/`**: el fetch y el estado de servidor viven en hooks (`hooks/`) o en el Server Component de la página, y bajan por props.
- **Componentes chicos:** si un archivo supera ~150 líneas, extraer subcomponentes o lógica a un hook.
- Cada carpeta puede tener un `index.ts` que exporte solo su API pública; se importa con alias: `import { Button } from "@/components/ui/button"`.

## Landing page

- Vive en el route group `(marketing)`: **estática (SSG), sin Clerk, sin llamadas al backend**. Rápida y buena para SEO.
- Cada sección es una carpeta en `components/marketing/<seccion>/`; `page.tsx` solo las compone en orden.
- El copy repetible (tools, FAQ, pasos) va en `content/` como arrays tipados, no hardcodeado en el JSX.
- Los CTA ("Conectar mi tienda") llevan a `/sign-in` → `/dashboard`.
- Metadata (title, description, Open Graph) con la Metadata API de Next en el layout/página.

## Autenticación (Clerk)

Clerk se usa **solo para quien quiere conectar su tienda y usar el MCP**. El visitante de la landing nunca pasa por Clerk.

- `ClerkProvider` envuelve solo el layout de `(app)`, no la raíz.
- `proxy.ts` usa `clerkMiddleware` + `createRouteMatcher` para proteger `/dashboard(.*)` y `/connect`. Todo lo demás es público.
- **`/connect/callback` queda fuera del middleware a propósito:** llega desde Tiendanube (navegación cross-site) y en esa request el middleware puede no ver la sesión. `useConnectCallback` espera a Clerk en el cliente; si no hay sesión, hace `redirectToSignIn` y vuelve a la misma URL con el `code` (dura 5 minutos).
- Clerk emite un **JWT** que se envía al backend en `Authorization: Bearer <token>`; FastAPI lo valida contra el JWKS.

## Flujo de conexión de tienda

1. En el dashboard, el usuario toca "Conectar tienda" → `GET /api/tiendanube/install-url` → redirect a Tiendanube.
2. Tiendanube vuelve a la Redirect URL del panel (`{API}/api/tiendanube/callback`, por ngrok en dev), que reenvía a `/connect/callback?code=...&state=...`.
3. La página llama a `POST /api/tiendanube/connect` con el `code` y redirige a `/dashboard`.
4. El usuario genera una API key (se muestra **una sola vez**) y copia el snippet de config MCP (`lib/mcp/`) para su cliente de IA.

## Conectar el asistente de IA (OAuth del MCP)

El mismo flujo sirve para Claude, ChatGPT, Gemini, Cursor o cualquier cliente MCP con OAuth (ver `backend/README.md`, "MCP: OAuth 2.1").

- **`/connect-ai`** (pública): guía paso a paso por asistente (pestañas Claude / Claude Code / ChatGPT / Otros) con la URL del conector para copiar (`NEXT_PUBLIC_MCP_URL`: ngrok en local, el dominio hosteado). Se llega desde "Mis tiendas", la pantalla de tienda conectada y el footer.
- **`/authorize?request_id=...`**: consentimiento. El backend redirige acá desde su `/authorize`; el usuario elige qué tienda compartir y se lo devuelve al asistente (`redirect_url` con `code`). Sin sesión, manda al login y vuelve (no se protege en el middleware: la navegación es cross-site).
- Componentes: `components/dashboard/authorize/` (consentimiento, mismo lenguaje visual que la conexión con Tiendanube: ícono del asistente ↔ mascota con la línea animada) y `components/dashboard/assistant-guide/`. Hook: `useAuthorizationRequest`. API: `lib/api/oauth.ts`.

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

## Layout de pantallas (sin espacios en blanco)

Regla obligatoria para toda pantalla nueva o rediseñada:

- **Navbar y footer en todas las páginas**, excepto login y registro (`/sign-in`, `/sign-up`).
- **Una pantalla llena el alto visible debajo de la navbar** con la utilidad `screen-fill` (`100dvh - --navbar-height`); el footer queda debajo del pliegue.
- **Ancho de la navbar (`max-w-6xl`)** para las pantallas con contenido (resultados, detalles, dashboards). Nada de un panel angosto (`max-w-lg`/`max-w-2xl`) centrado con aire vacío a los costados.
- **Si hay mucho contenido, se reparte en columnas** (ej. `lg:grid-cols-[2fr_3fr]`: mensaje + acciones a la izquierda, datos a la derecha) para que entre en la pantalla sin scroll. Nunca una columna angosta que sigue hacia abajo por debajo del pliegue.
- **Las pantallas de espera (cargando) son compactas**: panel chico centrado (`max-w-md`), no maximizado. Lo que llena la pantalla es el resultado (éxito/error).
- **Los skeletons replican la estructura del componente final** (mismos paddings, alto de cada línea de texto, grillas): la altura no puede saltar cuando llegan los datos. Ej. `StoreCardSkeleton`.
- **Poco margen debajo de la navbar** (`pt-4`): el contenido arranca pegado a ella, sin `py-12` de relleno.
- **El contenido nunca puede ensanchar la página** (cero scroll horizontal, en ningún ancho): las grillas con columnas `fr` usan `minmax(0,…)` (`lg:grid-cols-[minmax(0,2fr)_minmax(0,3fr)]`) y `grid-cols-1` en mobile; los hijos flex/grid con texto largo llevan `min-w-0`. URLs, comandos y código van en `CopyField` (una línea que se desliza), nunca sueltos.
- Paneles angostos centrados solo para formularios cortos o mensajes de una línea (login, 404).
- **Pantallas de espera: la mascota de carga** (`LoadingMascot` en `components/ui/loading-mascot/`), no spinners sueltos. Los spinners quedan solo dentro de botones.

## Reglas

- **`app/` solo orquesta.** Las páginas importan de `components/`, `lib/` y `content/`; sin lógica pesada.
- **`lib/` = todo lo reutilizable y sin UI.** Nunca JSX en `lib/`.
- **La landing no depende de Clerk ni del backend.** Si una sección necesita datos, salen de `content/`.
- **Server Components por defecto.** `"use client"` solo donde hay interactividad (forms, copiar al portapapeles, modales).
- **Toda llamada al backend pasa por `lib/api/`** y va directo a FastAPI.
- **Listados paginados en el backend** (`page` / `per_page`, ej. `/api/stores` de a 3): el front pide una página por vez y usa `Pagination` (`components/ui/pagination/`, íconos + números con "…"). Al cambiar de página se atenúa la anterior hasta que llega la nueva (sin skeleton, para que no salte la altura).
- **Tipos compartidos con la API en `lib/schemas/` (zod)**, derivados con `z.infer`.
- **Nunca loguear ni persistir API keys** en el cliente (ni `localStorage`). Se muestran una vez y listo.
- **Tailwind para todo el estilo**; variantes de componentes con `cn()`, sin clases inline gigantes repetidas.
