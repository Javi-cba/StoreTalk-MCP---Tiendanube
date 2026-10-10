"use client";

import { useAuth } from "@clerk/nextjs";
import { useCallback, useState } from "react";
import { ApiError } from "@/lib/api/client";
import { getInstallUrl } from "@/lib/api/stores";

/** Pide al backend la URL de autorización (con el JWT de Clerk) y redirige a Tiendanube. */
export function useStartConnect() {
  const { getToken } = useAuth();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<ApiError | null>(null);

  const start = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const url = await getInstallUrl(await getToken());
      // Queda en loading mientras el navegador sale hacia Tiendanube.
      window.location.assign(url);
    } catch (err) {
      setError(err instanceof ApiError ? err : new ApiError("unexpected_error", "No pudimos iniciar la conexión. Probá de nuevo.", 0));
      setLoading(false);
    }
  }, [getToken]);

  return { start, loading, error };
}
