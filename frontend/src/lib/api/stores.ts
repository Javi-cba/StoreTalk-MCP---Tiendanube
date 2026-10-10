import { z } from "zod";
import { apiRequest } from "@/lib/api/client";
import {
  connectedStoreSchema,
  installUrlSchema,
  storesPageSchema,
  type ConnectedStore,
  type ConnectStoreInput,
  type StoresPage,
} from "@/lib/schemas/stores";

/** URL de autorización de Tiendanube, con un `state` firmado para el usuario logueado. */
export async function getInstallUrl(token: string | null): Promise<string> {
  const { url } = await apiRequest("/api/tiendanube/install-url", { token, schema: installUrlSchema });
  return url;
}

/** Intercambia el `code` de Tiendanube por la conexión (el backend guarda token y scopes). */
export function connectStore(token: string | null, input: ConnectStoreInput): Promise<ConnectedStore> {
  return apiRequest("/api/tiendanube/connect", {
    token,
    schema: connectedStoreSchema,
    method: "POST",
    body: input,
  });
}

/** Tiendas por página por defecto: cada una es un request en vivo a Tiendanube. */
export const STORES_PER_PAGE = 3;

/** Una página de las tiendas conectadas del usuario, con sus datos en vivo de Tiendanube. */
export function listStores(token: string | null, page: number, perPage = STORES_PER_PAGE): Promise<StoresPage> {
  const query = new URLSearchParams({ page: String(page), per_page: String(perPage) });
  return apiRequest(`/api/stores?${query}`, { token, schema: storesPageSchema });
}

/** Desconecta una tienda: el backend borra sus credenciales de Tiendanube y revoca sus API keys. */
export async function disconnectStore(token: string | null, connectionId: string): Promise<void> {
  // 204 sin body: el cliente lo lee como null.
  await apiRequest(`/api/stores/${encodeURIComponent(connectionId)}`, {
    token,
    schema: z.null(),
    method: "DELETE",
  });
}
