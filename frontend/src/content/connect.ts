export type ConnectErrorAction = "reconnect" | "switch-account" | "home";

type ConnectErrorCopy = {
  title: string;
  /** Si falta, se muestra el mensaje que mandó el backend. */
  description?: string;
  actions: readonly ConnectErrorAction[];
};

export const connectCopy = {
  start: {
    metaTitle: "Conectar tienda",
    eyebrow: "Paso 1 de 2",
    title: "Conectá tu tienda Tiendanube",
    description:
      "Te llevamos a Tiendanube para que autorices a StoreTalk. Cuando aceptes, volvés acá con tu tienda lista para usar desde tu asistente de IA.",
    steps: [
      "Autorizás la app desde el admin de tu tienda.",
      "Guardamos el acceso cifrado, nunca tu contraseña.",
      "Podés desconectarla cuando quieras.",
    ],
    cta: "Conectar con Tiendanube",
  },
  callback: {
    metaTitle: "Conectando tienda",
    loadingTitle: "Conectando tu tienda…",
    loadingDescription: "Estamos validando la autorización con Tiendanube. No cierres esta pestaña.",
    mascotAlt: "La mascota de StoreTalk preparando la conexión con tu tienda",
  },
  success: {
    eyebrow: "Conexión exitosa",
    title: "¡Tu tienda está conectada!",
    mascotAlt: "La mascota festejando que tu tienda quedó conectada",
    description: "StoreTalk ya puede trabajar con tu tienda usando los permisos que aceptaste.",
    fallbackStoreName: "Tu tienda",
    detailsTitle: "Datos de la tienda",
    scopesTitle: "Permisos otorgados",
    scopesDescription: "Es lo que tu asistente de IA va a poder hacer en la tienda.",
    noScopes: "Tiendanube no informó permisos para esta conexión.",
    visitStore: "Ver tienda",
    connectAnother: "Conectar otra tienda",
    myStores: "Ver mis tiendas",
    home: "Volver al inicio",
  },
  details: {
    storeId: "ID de tienda",
    email: "Email",
    country: "País",
    language: "Idioma",
    currency: "Moneda",
    plan: "Plan",
  },
  error: {
    eyebrow: "No pudimos conectar tu tienda",
    codeLabel: "Código de error",
    actions: {
      reconnect: "Volver a conectar",
      "switch-account": "Usar otra cuenta",
      home: "Volver al inicio",
    } satisfies Record<ConnectErrorAction, string>,
  },
} as const;

const fallbackError: ConnectErrorCopy = {
  title: "Algo salió mal",
  actions: ["reconnect", "home"],
};

/** Qué mostrar y qué opciones dar según el código de error del backend. */
export const connectErrors: Record<string, ConnectErrorCopy> = {
  missing_code: {
    title: "No recibimos la autorización",
    description:
      "Tiendanube no nos devolvió el permiso de acceso. Puede que hayas cancelado la instalación o que el enlace esté incompleto.",
    actions: ["reconnect", "home"],
  },
  authorization_failed: {
    title: "La autorización venció",
    actions: ["reconnect", "home"],
  },
  invalid_state: {
    title: "El enlace no corresponde a esta sesión",
    actions: ["reconnect", "switch-account", "home"],
  },
  unauthenticated: {
    title: "Tu sesión terminó",
    actions: ["switch-account", "home"],
  },
  invalid_session: {
    title: "Tu sesión terminó",
    actions: ["switch-account", "home"],
  },
  network_error: {
    title: "Sin conexión con StoreTalk",
    actions: ["reconnect", "home"],
  },
  auth_unavailable: {
    title: "Servicio no disponible",
    actions: ["reconnect", "home"],
  },
};

export function getConnectError(code: string): ConnectErrorCopy {
  return connectErrors[code] ?? fallbackError;
}

/** Nombre legible de cada recurso de los scopes de Tiendanube (read_products → Productos). */
export const scopeResources: Record<string, string> = {
  products: "Productos",
  orders: "Órdenes",
  orders_risk: "Riesgo de fraude",
  draft_orders: "Órdenes borrador",
  fulfillment_orders: "Despachos",
  customers: "Clientes",
  coupons: "Cupones",
  discounts: "Promociones",
  content: "Contenido",
  shipping: "Envíos",
  locations: "Depósitos",
  logistics: "Logística",
  scripts: "Scripts",
  payments: "Pagos",
  abandoned_carts: "Carritos abandonados",
  domains: "Dominios",
  store: "Tienda",
};

export const scopeAccess = {
  read: "Ver",
  write: "Crear, editar y borrar",
} as const;
