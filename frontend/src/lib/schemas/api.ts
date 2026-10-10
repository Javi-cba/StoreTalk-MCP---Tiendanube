import { z } from "zod";

/** Error estándar del backend: { error: { code, message } } */
export const apiErrorBodySchema = z.object({
  error: z.object({ code: z.string(), message: z.string() }),
});
