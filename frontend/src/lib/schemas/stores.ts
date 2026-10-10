import { z } from "zod";

export const installUrlSchema = z.object({ url: z.url() });

export const connectedStoreSchema = z.object({
  connection_id: z.string(),
  store_id: z.number().int(),
  // unavailable: Tiendanube no respondió y solo hay datos guardados (nombre, idioma).
  status: z.enum(["active", "unavailable"]),
  name: z.string().nullable(),
  url: z.string().nullable(),
  domain: z.string().nullable(),
  email: z.string().nullable(),
  logo_url: z.string().nullable(),
  country: z.string().nullable(),
  language: z.string().nullable(),
  currency: z.string().nullable(),
  plan: z.string().nullable(),
  scopes: z.array(z.string()),
  connected_at: z.string(),
});

export type ConnectedStore = z.infer<typeof connectedStoreSchema>;

/** Una página de "Mis tiendas": el backend pagina y solo consulta en vivo las tiendas de esa página. */
export const storesPageSchema = z.object({
  stores: z.array(connectedStoreSchema),
  page: z.number().int().min(1),
  per_page: z.number().int().min(1),
  total: z.number().int().min(0),
  total_pages: z.number().int().min(1),
});

export type StoresPage = z.infer<typeof storesPageSchema>;

export type ConnectStoreInput = { code: string; state: string | null };
