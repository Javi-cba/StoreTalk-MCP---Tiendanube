/**
 * ¿Hay una sesión de Clerk en este navegador? Se responde sin cargar Clerk, leyendo la cookie
 * `__client_uat` que Clerk deja en el dominio de la app ("0" = sin sesión, timestamp = con sesión).
 * La cookie lleva un sufijo derivado de la publishable key (así lo calcula @clerk/shared), para no
 * confundirla con la de otra instancia de Clerk en el mismo dominio (pasa en localhost).
 */
const COOKIE_NAME = "__client_uat";

async function cookieSuffix(publishableKey: string): Promise<string> {
  const digest = await crypto.subtle.digest("SHA-1", new TextEncoder().encode(publishableKey));
  return btoa(String.fromCharCode(...new Uint8Array(digest)))
    .replace(/\+/g, "-")
    .replace(/\//g, "_")
    .slice(0, 8);
}

function readCookie(name: string): string | null {
  const entry = document.cookie.split("; ").find((cookie) => cookie.startsWith(`${name}=`));
  return entry ? entry.slice(name.length + 1) : null;
}

export async function hasClerkSession(): Promise<boolean> {
  const publishableKey = process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY;
  if (!publishableKey) return false;
  try {
    const suffixed = readCookie(`${COOKIE_NAME}_${await cookieSuffix(publishableKey)}`);
    const value = suffixed ?? readCookie(COOKIE_NAME);
    return value !== null && value !== "0";
  } catch {
    return false;
  }
}
