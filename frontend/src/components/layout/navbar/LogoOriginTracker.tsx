"use client";

import { useEffect } from "react";
import { AUTH_PATHS, saveLogoOrigin } from "@/lib/auth/logoOrigin";

/**
 * Al tocar un link hacia el login, guarda dónde está el logo del navbar para que la pantalla
 * de login lo anime desde ahí hasta su lugar (en vez de que aparezca de golpe).
 */
export function LogoOriginTracker() {
  useEffect(() => {
    function handleClick(event: MouseEvent) {
      const anchor = (event.target as Element | null)?.closest("a");
      if (!anchor || anchor.origin !== window.location.origin) return;
      if (!AUTH_PATHS.some((path) => anchor.pathname.startsWith(path))) return;
      const logo = document.querySelector("[data-brand-logo]");
      if (logo) saveLogoOrigin(logo.getBoundingClientRect());
    }
    document.addEventListener("click", handleClick, { capture: true });
    return () => document.removeEventListener("click", handleClick, { capture: true });
  }, []);

  return null;
}
