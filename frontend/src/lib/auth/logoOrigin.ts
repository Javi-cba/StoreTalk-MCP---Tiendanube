import { mascotReplaySrc } from "@/lib/utils/mascot";

/** Posición del logo del navbar al salir hacia el login, para animarlo hasta su lugar nuevo. */
export type LogoOrigin = { x: number; y: number; width: number; height: number; replayKey: number };

const STORAGE_KEY = "storetalk:logo-origin";
// Si la navegación tardó más que esto (o es un reload), se hace la intro de entrada directa.
const MAX_AGE_MS = 5000;

export const AUTH_PATHS = ["/sign-in", "/sign-up", "/connect"];

export function saveLogoOrigin(rect: DOMRect) {
  try {
    const replayKey = Date.now();
    // Se precarga ya: así la mascota se ve durante todo el viaje y saluda desde el primer frame.
    new Image().src = mascotReplaySrc(replayKey);
    const origin: LogoOrigin & { at: number } = {
      x: rect.x,
      y: rect.y,
      width: rect.width,
      height: rect.height,
      replayKey,
      at: replayKey,
    };
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify(origin));
  } catch {
    // Sin sessionStorage no hay animación desde el navbar; queda la intro directa.
  }
}

export function consumeLogoOrigin(): LogoOrigin | null {
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY);
    sessionStorage.removeItem(STORAGE_KEY);
    if (!raw) return null;
    const { at, ...origin } = JSON.parse(raw) as LogoOrigin & { at: number };
    return Date.now() - at <= MAX_AGE_MS ? origin : null;
  } catch {
    return null;
  }
}
