"use client";

import { useAuth } from "@clerk/nextjs";
import { useCallback, useEffect, useState } from "react";
import { ApiError } from "@/lib/api/client";
import { listStores } from "@/lib/api/stores";
import type { StoresPage } from "@/lib/schemas/stores";

export type StoresState =
  | { status: "loading" }
  | { status: "ready"; data: StoresPage }
  | { status: "error"; message: string };

/**
 * Tiendas del usuario logueado, de a una página (GET /api/stores?page=N con el JWT de Clerk).
 * Al cambiar de página se sigue mostrando la anterior con `pending` hasta que llega la nueva.
 */
export function useStores() {
  const { isLoaded, getToken } = useAuth();
  const [state, setState] = useState<StoresState>({ status: "loading" });
  const [page, setPage] = useState(1);
  const [pending, setPending] = useState(false);
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    if (!isLoaded) return;
    let active = true;
    (async () => {
      try {
        const data = await listStores(await getToken(), page);
        if (!active) return;
        // La página quedó fuera de rango (ej. se revocaron tiendas): vamos a la última que existe.
        if (data.stores.length === 0 && data.total > 0 && page > data.total_pages) {
          setPage(data.total_pages);
          return;
        }
        setState({ status: "ready", data });
      } catch (err) {
        const message = err instanceof ApiError ? err.message : "Ocurrió un error inesperado.";
        if (active) setState({ status: "error", message });
      } finally {
        if (active) setPending(false);
      }
    })();
    return () => {
      active = false;
    };
  }, [isLoaded, getToken, page, attempt]);

  const goToPage = useCallback((next: number) => {
    setPending(true);
    setPage(next);
  }, []);

  const retry = useCallback(() => {
    setState({ status: "loading" });
    setAttempt((n) => n + 1);
  }, []);

  /** Vuelve a pedir la página actual sin pasar por el skeleton (ej. después de desconectar una tienda). */
  const refresh = useCallback(() => {
    setPending(true);
    setAttempt((n) => n + 1);
  }, []);

  return { state, page, pending, goToPage, retry, refresh };
}
