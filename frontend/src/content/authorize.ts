/** Pantalla de consentimiento: un asistente de IA pide acceso a una tienda vía MCP (OAuth). */
export const authorizeCopy = {
  metaTitle: "Autorizar asistente de IA",
  loading: {
    title: "Preparando la conexión…",
    description: "Estamos verificando el pedido de tu asistente de IA.",
    mascotAlt: "La mascota de StoreTalk preparando la conexión",
  },
  consent: {
    eyebrow: "Conexión con tu asistente",
    title: (client: string) => `${client} quiere manejar tu tienda`,
    description: "Elegí qué tienda puede usar. La podés desconectar cuando quieras desde Mis tiendas.",
    returnsTo: "Al permitir vas a volver a",
    canTitle: "Va a poder",
    can: [
      "Consultar y editar productos, categorías, cupones y órdenes de la tienda que elijas.",
      "Solo lo que permiten los accesos que diste en Tiendanube.",
      "Nunca ve tu contraseña ni tus otras tiendas.",
    ],
    storesTitle: "¿Qué tienda querés conectar?",
    fallbackStoreName: "Tu tienda",
    storeId: "ID",
    permissions: (count: number) => (count === 1 ? "1 permiso" : `${count} permisos`),
    approve: "Permitir acceso",
    deny: "Cancelar",
    trustHint: "Permití solo si vos iniciaste esta conexión desde tu asistente de IA.",
  },
  noStores: {
    title: "Primero conectá una tienda",
    description:
      "Para que tu asistente pueda trabajar necesitás una tienda Tiendanube conectada. Conectala y volvé a intentarlo desde tu asistente.",
    cta: "Conectar mi tienda",
    deny: "Cancelar y volver",
  },
  done: {
    approved: {
      eyebrow: "Conexión exitosa",
      title: (client: string) => `¡Listo! ${client} ya puede usar tu tienda`,
      description: "Te estamos devolviendo a tu asistente…",
      mascotAlt: "La mascota festejando la conexión con tu asistente",
    },
    denied: {
      eyebrow: "Conexión cancelada",
      title: "No compartiste ninguna tienda",
      description: "Te estamos devolviendo a tu asistente…",
    },
    manual: "Si no vuelve solo, tocá acá",
  },
  error: {
    eyebrow: "No pudimos conectar tu asistente",
    title: "El pedido de conexión no es válido",
    missing: "Falta el pedido de conexión. Empezá de nuevo desde tu asistente de IA.",
    guide: "Ver cómo conectar",
    home: "Ir a Mis tiendas",
  },
} as const;
