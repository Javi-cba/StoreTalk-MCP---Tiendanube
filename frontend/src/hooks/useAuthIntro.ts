"use client";

import { useLayoutEffect, useRef, useState, type RefObject } from "react";
import { consumeLogoOrigin, type LogoOrigin } from "@/lib/auth/logoOrigin";

/**
 * - from-navbar: se llegó tocando un link del homepage; el logo viaja desde el navbar.
 * - direct: se entró por URL; la mascota saluda en el centro y después se acomoda.
 * - static: el usuario pidió menos movimiento.
 */
export type AuthIntroMode = "pending" | "from-navbar" | "direct" | "static";

const DOCK_EASING = "cubic-bezier(0.65, 0, 0.35, 1)";
const FROM_NAVBAR_MS = 800;
// Igual que el intro del homepage: ~2.1 s de caída + saludo en el centro y 0.7 s hasta su lugar.
const DIRECT_MS = 2800;
const DIRECT_HOLD = 0.75;
const DIRECT_SCALE = 1.6;

type IntroState = { mode: AuthIntroMode; replayKey?: number };

/** Anima el logo (FLIP con Web Animations) hasta la posición en la que quedó en el layout. */
export function useAuthIntro(markRef: RefObject<HTMLElement | null>): IntroState {
  const [state, setState] = useState<IntroState>({ mode: "pending" });
  // Se lee una sola vez: en StrictMode el efecto corre dos veces y el origen ya estaría consumido.
  const origin = useRef<LogoOrigin | null | undefined>(undefined);

  useLayoutEffect(() => {
    const mark = markRef.current;
    if (!mark) return;
    if (origin.current === undefined) origin.current = consumeLogoOrigin();

    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      // eslint-disable-next-line react-hooks/set-state-in-effect -- depende de medir el DOM antes del paint
      setState({ mode: "static" });
      return;
    }

    const box = mark.getBoundingClientRect();
    const centerX = box.x + box.width / 2;
    const centerY = box.y + box.height / 2;
    const from = origin.current;
    let animation: Animation;

    if (from) {
      const start = `translate(${from.x + from.width / 2 - centerX}px, ${from.y + from.height / 2 - centerY}px) scale(${from.height / box.height})`;
      animation = mark.animate([{ transform: start }, { transform: "none" }], {
        duration: FROM_NAVBAR_MS,
        easing: DOCK_EASING,
        fill: "backwards",
      });
      setState({ mode: "from-navbar", replayKey: from.replayKey });
    } else {
      const start = `translate(${window.innerWidth / 2 - centerX}px, ${window.innerHeight / 2 - centerY}px) scale(${DIRECT_SCALE})`;
      animation = mark.animate(
        [
          { transform: start, offset: 0 },
          { transform: start, offset: DIRECT_HOLD, easing: DOCK_EASING },
          { transform: "none", offset: 1 },
        ],
        { duration: DIRECT_MS, fill: "backwards" },
      );
      setState({ mode: "direct", replayKey: Date.now() });
    }

    return () => animation.cancel();
  }, [markRef]);

  return state;
}

/** Clases para el recuadro del formulario: aparece cuando el logo terminó de llegar a su lugar. */
export function introCardClass(mode: AuthIntroMode): string {
  if (mode === "pending") return "opacity-0";
  if (mode === "direct") return "animate-intro-card";
  if (mode === "from-navbar") return "animate-intro-card [animation-delay:800ms]"; // = FROM_NAVBAR_MS
  return "";
}

/** Clases para el resto de la pantalla: aparece cuando el logo ya está llegando a su lugar. */
export function introRevealClass(mode: AuthIntroMode): string {
  if (mode === "pending") return "opacity-0";
  if (mode === "direct") return "animate-intro-content";
  if (mode === "from-navbar") return "animate-rise-in [animation-delay:350ms]";
  return "";
}
