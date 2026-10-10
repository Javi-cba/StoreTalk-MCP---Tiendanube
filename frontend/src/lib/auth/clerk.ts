import { esUY } from "@clerk/localizations";

/** Después de loguearse va a sus tiendas (sin tiendas, ahí mismo está el botón para conectar). */
export const AFTER_AUTH_URL = "/dashboard";

export const clerkLocalization = esUY;

/** Componentes de Clerk que quedan (menú de cuenta) con los colores de la marca. */
export const clerkAppearance = {
  variables: {
    colorPrimary: "#2563eb",
    borderRadius: "0.875rem",
    fontFamily: "var(--font-geist-sans), sans-serif",
  },
};
