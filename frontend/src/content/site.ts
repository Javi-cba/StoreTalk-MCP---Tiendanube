export const site = {
  name: "StoreTalk",
  description: "Conecta tu tienda Tiendanube a tu asistente de IA vía MCP.",
} as const;

export const navigation = {
  signIn: { label: "Ingresar", href: "/sign-in" },
  cta: { label: "Conectar mi tienda", href: "/connect" },
  // Reemplaza al CTA cuando ya hay sesión.
  dashboard: { label: "Mis tiendas", href: "/dashboard" },
  connectAi: { label: "Conectar mi IA", href: "/connect-ai" },
  signOut: { label: "Salir" },
} as const;

export const footer = {
  tagline: "Tu Tiendanube, a una conversación de distancia. Compatible con Claude, ChatGPT, Cursor y cualquier cliente MCP.",
  columns: [
    {
      title: "Producto",
      links: [
        { label: "Conectar mi tienda", href: "/connect" },
        { label: "Conectar mi IA", href: "/connect-ai" },
      ],
    },
    {
      title: "Cuenta",
      links: [{ label: "Ingresar", href: "/sign-in" }],
    },
  ],
  author: {
    prefix: "Powered by",
    name: "Javier Córdoba",
    portfolio: { label: "Portfolio", href: "https://main.d3daopq1z2wvo3.amplifyapp.com/" },
    linkedin: { label: "LinkedIn", href: "https://www.linkedin.com/in/javi-cba/" },
  },
} as const;
