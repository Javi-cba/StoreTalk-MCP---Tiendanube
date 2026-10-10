"use client";

import { useAuth, useClerk } from "@clerk/nextjs";
import { useCallback, useEffect, useRef, useState } from "react";
import { ApiError } from "@/lib/api/client";
import { approveAuthorization, denyAuthorization, getAuthorizationRequest } from "@/lib/api/oauth";
import type { AuthorizationRequest } from "@/lib/schemas/oauth";

/** Tiempo para ver el festejo antes de volver al asistente. */
const REDIRECT_DELAY_MS = 1800;

export type AuthorizeState =
  | { status: "loading" }
  | { status: "ready"; request: AuthorizationRequest; submitting: "approve" | "deny" | null; error: string | null }
  | { status: "redirecting"; outcome: "approved" | "denied"; request: AuthorizationRequest; url: string }
  | { status: "error"; code: string; message: string };

function toApiError(err: unknown): ApiError {
  return err instanceof ApiError ? err : new ApiError("unexpected_error", "Ocurrió un error inesperado.", 0);
}

/**
 * Pantalla de consentimiento del OAuth del MCP (/authorize?request_id=...). Llega desde el
 * asistente (navegación cross-site), así que la sesión se verifica acá y no en el middleware.
 */
export function useAuthorizationRequest(requestId: string | null) {
  const { isLoaded, isSignedIn, getToken } = useAuth();
  const clerk = useClerk();
  const [state, setState] = useState<AuthorizeState>({ status: "loading" });
  const started = useRef(false);

  useEffect(() => {
    if (!isLoaded || !requestId || started.current) return;
    started.current = true;

    if (!isSignedIn) {
      void clerk.redirectToSignIn({ signInForceRedirectUrl: window.location.href });
      return;
    }

    (async () => {
      try {
        const request = await getAuthorizationRequest(await getToken(), requestId);
        setState({ status: "ready", request, submitting: null, error: null });
      } catch (err) {
        const apiError = toApiError(err);
        setState({ status: "error", code: apiError.code, message: apiError.message });
      }
    })();
  }, [isLoaded, isSignedIn, clerk, getToken, requestId]);

  // El navegador vuelve al asistente después de mostrar el resultado.
  useEffect(() => {
    if (state.status !== "redirecting") return;
    const timer = window.setTimeout(() => window.location.assign(state.url), REDIRECT_DELAY_MS);
    return () => window.clearTimeout(timer);
  }, [state]);

  const decide = useCallback(
    async (decision: "approve" | "deny", connectionId?: string) => {
      if (state.status !== "ready" || !requestId) return;
      const { request } = state;
      setState({ ...state, submitting: decision, error: null });
      try {
        const token = await getToken();
        const url =
          decision === "approve" && connectionId
            ? await approveAuthorization(token, requestId, connectionId)
            : await denyAuthorization(token, requestId);
        setState({ status: "redirecting", outcome: decision === "approve" ? "approved" : "denied", request, url });
      } catch (err) {
        const apiError = toApiError(err);
        // Pedido vencido: ya no se puede reintentar desde acá.
        if (apiError.code === "authorization_expired") {
          setState({ status: "error", code: apiError.code, message: apiError.message });
          return;
        }
        setState({ status: "ready", request, submitting: null, error: apiError.message });
      }
    },
    [state, requestId, getToken],
  );

  if (!requestId) return { state: { status: "error", code: "missing_request", message: "" } as AuthorizeState, decide };
  return { state, decide };
}
