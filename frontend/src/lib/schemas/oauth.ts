import { z } from "zod";

/** Pedido de un asistente de IA (Claude, ChatGPT...) para acceder a una tienda vía MCP. */
export const authorizationRequestSchema = z.object({
  id: z.string(),
  client: z.object({
    name: z.string(),
    // A dónde vuelve el navegador al aprobar (ej. claude.ai).
    redirect_host: z.string(),
  }),
  stores: z.array(
    z.object({
      connection_id: z.string(),
      store_id: z.number().int(),
      name: z.string().nullable(),
      scopes: z.array(z.string()),
    }),
  ),
  expires_at: z.string(),
});

export type AuthorizationRequest = z.infer<typeof authorizationRequestSchema>;
export type ConsentStore = AuthorizationRequest["stores"][number];

export const authorizationDecisionSchema = z.object({ redirect_url: z.url() });
