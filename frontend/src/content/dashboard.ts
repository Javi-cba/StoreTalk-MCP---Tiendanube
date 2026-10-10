export const dashboardCopy = {
  metaTitle: "Mis tiendas",
  eyebrow: "Tu cuenta",
  title: "Mis tiendas",
  description: "Las tiendas que conectaste a StoreTalk, con sus datos y los permisos que otorgaste.",
  connectAnother: "Conectar otra tienda",
  connectFirst: "Conectar mi primera tienda",
  empty: {
    title: "Todavía no conectaste ninguna tienda",
    description: "Conectá tu Tiendanube para empezar a manejarla desde tu asistente de IA.",
  },
  error: {
    title: "No pudimos cargar tus tiendas",
    retry: "Reintentar",
  },
  card: {
    connectedAt: "Conectada el",
    status: {
      active: "Conectada",
      unavailable: "Sin respuesta de Tiendanube",
    },
    unavailableHint: "Tiendanube no respondió a tiempo; mostramos los datos que tenemos guardados.",
    scopesTitle: "Permisos otorgados",
    noScopes: "Tiendanube no informó permisos para esta conexión.",
    disconnect: "Desconectar tienda",
  },
  disconnectDialog: {
    title: "¿Desconectar esta tienda?",
    description: (store: string) =>
      `Vamos a borrar las credenciales de ${store} y a desactivar sus API keys: tu asistente de IA deja de poder usarla al instante. Podés volver a conectarla cuando quieras.`,
    uninstallHint: "Si querés quitar la app por completo, desinstalala también desde el admin de Tiendanube.",
    confirm: "Sí, desconectar",
    cancel: "Cancelar",
  },
  loadingLabel: "Cargando tus tiendas",
  pagination: {
    nav: "Páginas de tiendas",
    first: "Primera página",
    previous: "Página anterior",
    next: "Página siguiente",
    last: "Última página",
    page: (page: number) => `Página ${page}`,
    range: (from: number, to: number, total: number) => `Tiendas ${from}–${to} de ${total}`,
  },
} as const;
