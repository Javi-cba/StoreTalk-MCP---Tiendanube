import { apiRequest } from "@/lib/api/client";
import { authorizationDecisionSchema, authorizationRequestSchema, type AuthorizationRequest } from "@/lib/schemas/oauth";

const base = (id: string) => `/api/oauth/authorizations/${encodeURIComponent(id)}`;

/** Quién pide acceso y entre qué tiendas del usuario puede elegir. */
export function getAuthorizationRequest(token: string | null, id: string): Promise<AuthorizationRequest> {
  return apiRequest(base(id), { token, schema: authorizationRequestSchema });
}

/** Aprueba con la tienda elegida; devuelve la URL del asistente (con el code) a la que hay que volver. */
export async function approveAuthorization(token: string | null, id: string, connectionId: string): Promise<string> {
  const { redirect_url } = await apiRequest(`${base(id)}/approve`, {
    token,
    schema: authorizationDecisionSchema,
    method: "POST",
    body: { connection_id: connectionId },
  });
  return redirect_url;
}

/** Cancela; devuelve la URL del asistente con error=access_denied. */
export async function denyAuthorization(token: string | null, id: string): Promise<string> {
  const { redirect_url } = await apiRequest(`${base(id)}/deny`, {
    token,
    schema: authorizationDecisionSchema,
    method: "POST",
  });
  return redirect_url;
}
