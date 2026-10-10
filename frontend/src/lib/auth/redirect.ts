import { AFTER_AUTH_URL } from "@/lib/auth/clerk";

const STORAGE_KEY = "storetalk:after-auth";

/**
 * Clerk manda `?redirect_url=<url absoluta>` cuando protege una ruta (ej. /connect/callback?code=...).
 * Solo se acepta el mismo origen, para no convertir el login en un open redirect.
 */
export function safeRedirectPath(value: string | null): string {
  if (!value || typeof window === "undefined") return AFTER_AUTH_URL;
  try {
    const url = new URL(value, window.location.origin);
    if (url.origin !== window.location.origin) return AFTER_AUTH_URL;
    if (url.pathname.startsWith("/sign-in") || url.pathname.startsWith("/sign-up")) return AFTER_AUTH_URL;
    return `${url.pathname}${url.search}${url.hash}`;
  } catch {
    return AFTER_AUTH_URL;
  }
}

/** El OAuth sale del sitio: se guarda a dónde volver para usarlo en /sso-callback. */
export function rememberAfterAuth(path: string) {
  try {
    sessionStorage.setItem(STORAGE_KEY, path);
  } catch {
    // sessionStorage bloqueado: se vuelve al destino por defecto.
  }
}

/** Lee el destino guardado sin borrarlo (para pasarlo al registro si no había cuenta). */
export function peekAfterAuth(): string | null {
  try {
    return sessionStorage.getItem(STORAGE_KEY);
  } catch {
    return null;
  }
}

export function consumeAfterAuth(): string {
  try {
    const path = sessionStorage.getItem(STORAGE_KEY);
    sessionStorage.removeItem(STORAGE_KEY);
    return safeRedirectPath(path);
  } catch {
    return AFTER_AUTH_URL;
  }
}
