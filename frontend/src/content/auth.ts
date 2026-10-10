type AuthPageCopy = {
  metaTitle: string;
  title: string;
  description: string;
  switchPrompt: string;
  switchLink: { label: string; href: string };
};

export type AuthFlow = "signIn" | "signUp";

export const authCopy = {
  signIn: {
    metaTitle: "Ingresar",
    title: "¡Hola de nuevo!",
    description: "Ingresá para conectar tu Tiendanube y manejarla desde tu asistente de IA.",
    switchPrompt: "¿Todavía no tenés cuenta?",
    switchLink: { label: "Creá una gratis", href: "/sign-up" },
  } satisfies AuthPageCopy,
  signUp: {
    metaTitle: "Crear cuenta",
    title: "Creá tu cuenta",
    description: "Es gratis. En un minuto conectás tu Tiendanube y empezás a hablarle a tu tienda.",
    switchPrompt: "¿Ya tenés cuenta?",
    switchLink: { label: "Ingresá", href: "/sign-in" },
  } satisfies AuthPageCopy,
  providers: {
    oauth_google: "Continuar con Google",
    oauth_apple: "Continuar con Apple",
  },
  privacy: "Solo usamos tu cuenta para identificarte. Nunca publicamos nada en tu nombre.",
  back: "Volver al inicio",
  notices: {
    noAccount:
      "No encontramos una cuenta con ese email. Creala acá con el mismo proveedor: es gratis y tarda un minuto.",
  },
  errors: {
    generic: "No pudimos completar el ingreso. Probá de nuevo en unos segundos.",
    verification:
      "Tu cuenta necesita un paso de verificación extra. Probá de nuevo o usá el otro proveedor.",
  },
  callback: {
    metaTitle: "Ingresando",
    title: "Terminando de ingresar…",
    description: "Un segundo, estamos preparando tu cuenta.",
    imageAlt: "Nuestra mascota esperando a que termine el ingreso",
  },
} as const;

export type OAuthProvider = keyof typeof authCopy.providers;
