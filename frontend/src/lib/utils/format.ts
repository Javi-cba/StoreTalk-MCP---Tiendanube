function displayName(type: "language" | "region", code: string | null): string | null {
  if (!code) return null;
  try {
    const name = new Intl.DisplayNames(["es"], { type }).of(code);
    return name ? name.charAt(0).toUpperCase() + name.slice(1) : code;
  } catch {
    return code;
  }
}

/** "es" → "Español". */
export const formatLanguage = (code: string | null) => displayName("language", code);

/** "AR" → "Argentina". */
export const formatCountry = (code: string | null) => displayName("region", code);

/** "https://mitienda.com.ar/" → "mitienda.com.ar". */
export function formatHost(url: string | null): string | null {
  if (!url) return null;
  try {
    return new URL(url.startsWith("http") ? url : `https://${url}`).host;
  } catch {
    return url;
  }
}

/** "2026-10-01T…" → "1 de octubre de 2026". */
export function formatDate(iso: string): string {
  const date = new Date(iso);
  return Number.isNaN(date.getTime())
    ? iso
    : new Intl.DateTimeFormat("es-AR", { day: "numeric", month: "long", year: "numeric" }).format(date);
}
