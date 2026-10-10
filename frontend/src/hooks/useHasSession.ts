"use client";

import { useEffect, useState } from "react";
import { hasClerkSession } from "@/lib/auth/session";

/** Sesión de Clerk sin cargar Clerk (para la landing). `null` mientras no se sabe. */
export function useHasSession(): boolean | null {
  const [signedIn, setSignedIn] = useState<boolean | null>(null);

  useEffect(() => {
    let active = true;
    const check = () => hasClerkSession().then((value) => active && setSignedIn(value));
    check();
    // Si inició o cerró sesión en otra pestaña, se actualiza al volver.
    window.addEventListener("focus", check);
    return () => {
      active = false;
      window.removeEventListener("focus", check);
    };
  }, []);

  return signedIn;
}
