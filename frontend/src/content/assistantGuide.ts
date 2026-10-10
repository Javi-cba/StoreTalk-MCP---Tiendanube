export type AssistantClientId = "claude" | "claude-code" | "chatgpt" | "other";

type GuideStep = {
  title: string;
  description: string;
  /** Comando para copiar (ej. Claude Code). `{url}` se reemplaza por la URL del MCP. */
  command?: string;
};

type AssistantClientGuide = {
  id: AssistantClientId;
  label: string;
  /** Dónde funciona una vez conectado. */
  availability: string;
  steps: GuideStep[];
};

/** Guía "Conectá tu IA": el mismo servidor MCP + OAuth sirve para cualquier cliente compatible. */
export const assistantGuideCopy = {
  metaTitle: "Conectá tu asistente de IA",
  eyebrow: "Paso 2 de 2",
  title: "Conectá tu tienda a tu asistente de IA",
  description:
    "Funciona con cualquier asistente compatible con MCP: pegás una URL, iniciás sesión y elegís la tienda.",
  urlLabel: "URL del conector",
  urlHint: "Es la misma para todos los asistentes.",
  copy: "Copiar",
  copied: "¡Copiada!",
  copyCommand: "Copiar comando",
  benefitsTitle: "Qué vas a poder hacer",
  benefits: [
    "Pedirle en lenguaje natural que cree, edite o busque productos.",
    "Revisar órdenes, cupones y categorías sin entrar al admin.",
    "Usarlo escribiendo o por voz, desde la compu o el celular.",
  ],
  examplesTitle: "Probá pedirle",
  examples: [
    "¿Cuál es mi producto más caro?",
    "Creá un cupón del 15% para la categoría Remeras",
    "¿Qué órdenes quedaron abiertas esta semana?",
  ],
  clientsLabel: "Elegí tu asistente",
  stepsTitle: "Paso a paso",
  menuNote: "Los nombres de los menús pueden cambiar un poco según la versión de la app.",
  security: "Solo compartís la tienda que elijas y podés desconectarla cuando quieras desde Mis tiendas.",
  clients: [
    {
      id: "claude",
      label: "Claude",
      availability: "Web, app de escritorio y celular (también por voz)",
      steps: [
        {
          title: "Abrí los conectores",
          description: "En claude.ai o en la app andá a Configuración → Conectores.",
        },
        {
          title: "Agregá un conector personalizado",
          description: "Tocá «Agregar conector personalizado». Como nombre poné StoreTalk y pegá la URL del conector.",
        },
        {
          title: "Conectá e iniciá sesión",
          description:
            "Tocá «Conectar». Se abre StoreTalk: iniciá sesión, elegí tu tienda y tocá «Permitir acceso».",
        },
        {
          title: "¡Listo! Hablale a tu tienda",
          description:
            "En un chat nuevo activá StoreTalk desde el menú (+) y pedile lo que necesites, escribiendo o por voz.",
        },
      ],
    },
    {
      id: "claude-code",
      label: "Claude Code",
      availability: "Terminal",
      steps: [
        {
          title: "Agregá el servidor",
          description: "En tu terminal corré este comando:",
          command: "claude mcp add --transport http storetalk {url}",
        },
        {
          title: "Iniciá sesión",
          description: "Dentro de Claude Code escribí /mcp, elegí storetalk y «Authenticate». Se abre StoreTalk en el navegador.",
        },
        {
          title: "Elegí la tienda",
          description: "Iniciá sesión, elegí la tienda y tocá «Permitir acceso». Volvé a la terminal: ya está conectado.",
        },
      ],
    },
    {
      id: "chatgpt",
      label: "ChatGPT",
      availability: "Web y app (según tu plan)",
      steps: [
        {
          title: "Abrí los conectores",
          description:
            "En ChatGPT andá a Configuración → Apps y conectores. Si hace falta, activá el modo desarrollador en Configuración avanzada.",
        },
        {
          title: "Creá el conector",
          description: "Tocá «Crear», poné StoreTalk como nombre, pegá la URL del conector y elegí OAuth como autenticación.",
        },
        {
          title: "Iniciá sesión y elegí la tienda",
          description: "Se abre StoreTalk: iniciá sesión, elegí tu tienda y tocá «Permitir acceso».",
        },
      ],
    },
    {
      id: "other",
      label: "Otros",
      availability: "Gemini CLI, Cursor y cualquier cliente MCP con OAuth",
      steps: [
        {
          title: "Buscá dónde agregar un servidor MCP",
          description: "Suele estar en Configuración → MCP, Conectores o Integraciones.",
        },
        {
          title: "Agregalo como servidor remoto (HTTP)",
          description: "Pegá la URL del conector. La autenticación es OAuth: no hace falta ninguna clave.",
        },
        {
          title: "Iniciá sesión y elegí la tienda",
          description:
            "Cuando se abra StoreTalk, iniciá sesión, elegí tu tienda y tocá «Permitir acceso». La app web de Gemini por ahora solo permite conectores de su catálogo: usá Gemini CLI.",
        },
      ],
    },
  ] satisfies AssistantClientGuide[],
} as const;
