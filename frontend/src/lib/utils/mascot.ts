export const MASCOT_SRC = "/brand/mascot-animated.webp";
export const MASCOT_LOADING_SRC = "/brand/mascot-loading.webp";

/**
 * El navegador comparte la animación entre imágenes con la misma URL: para que la mascota vuelva
 * a caer y saludar, cada repetición usa una URL propia.
 */
export function mascotReplaySrc(replayKey?: number): string {
  return replayKey ? `${MASCOT_SRC}?replay=${replayKey}` : MASCOT_SRC;
}
