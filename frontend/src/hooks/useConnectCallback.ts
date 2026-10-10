"use client";

import { useAuth, useClerk } from "@clerk/nextjs";
import { useSearchParams } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { ApiError } from "@/lib/api/client";
import { connectStore } from "@/lib/api/stores";
import type { ConnectedStore } from "@/lib/schemas/stores";

export type ConnectCallbackState =
  | { status: "loading" }
  | { status: "success"; store: ConnectedStore }
  | { status: "error"; code: string; message: string };

/** Toma el `code` que dejó Tiendanube en la URL y lo canjea en el backend una sola vez. */
export function useConnectCallback(): ConnectCallbackState {
  const searchParams = useSearchParams();
  const { isLoaded, isSignedIn, getToken } = useAuth();
  const clerk = useClerk();
  const [state, setState] = useState<ConnectCallbackState>({ status: "loading" });
  // El code es de un solo uso: evita el doble request (StrictMode, re-renders).
  const requested = useRef(false);

  const code = searchParams.get("code");
  const oauthState = searchParams.get("state");

  useEffect(() => {
    if (!isLoaded || !code || requested.current) return;
    requested.current = true;

    // Sin sesión: login y vuelta a esta misma URL (con el code, que dura 5 minutos).
    if (!isSignedIn) {
      void clerk.redirectToSignIn({ signInForceRedirectUrl: window.location.href });
      return;
    }

    (async () => {
      try {
        const store = await connectStore(await getToken(), { code, state: oauthState });
        setState({ status: "success", store });
      } catch (err) {
        const apiError =
          err instanceof ApiError ? err : new ApiError("unexpected_error", "Ocurrió un error inesperado.", 0);
        setState({ status: "error", code: apiError.code, message: apiError.message });
      }
    })();
  }, [isLoaded, isSignedIn, clerk, getToken, code, oauthState]);

  // Sin code no hay nada que canjear (instalación cancelada o URL incompleta).
  if (!code) return { status: "error", code: "missing_code", message: "" };
  return state;
}
