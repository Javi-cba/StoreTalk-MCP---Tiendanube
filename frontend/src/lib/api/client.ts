import type { z } from "zod";
import { apiErrorBodySchema } from "@/lib/schemas/api";

const API_URL = (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000").replace(/\/$/, "");

export class ApiError extends Error {
  constructor(
    readonly code: string,
    message: string,
    readonly status: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

type RequestOptions<T> = {
  /** JWT de Clerk (useAuth().getToken() o auth().getToken()). */
  token: string | null;
  schema: z.ZodType<T>;
  method?: "GET" | "POST" | "DELETE";
  body?: unknown;
};

/** fetch hacia FastAPI: agrega el Bearer, parsea el error estándar y valida la respuesta. */
export async function apiRequest<T>(path: string, { token, schema, method = "GET", body }: RequestOptions<T>): Promise<T> {
  if (!token) {
    throw new ApiError("unauthenticated", "Tu sesión venció. Volvé a iniciar sesión.", 401);
  }

  let response: Response;
  try {
    response = await fetch(`${API_URL}${path}`, {
      method,
      headers: {
        Authorization: `Bearer ${token}`,
        ...(body === undefined ? {} : { "Content-Type": "application/json" }),
      },
      body: body === undefined ? undefined : JSON.stringify(body),
      cache: "no-store",
    });
  } catch {
    throw new ApiError(
      "network_error",
      "No pudimos conectarnos. Revisá tu conexión e intentá de nuevo.",
      0,
    );
  }

  const data: unknown = await response.json().catch(() => null);

  if (!response.ok) {
    const parsed = apiErrorBodySchema.safeParse(data);
    if (parsed.success) {
      throw new ApiError(parsed.data.error.code, parsed.data.error.message, response.status);
    }
    throw new ApiError("unexpected_error", "Ocurrió un error inesperado. Probá de nuevo en unos minutos.", response.status);
  }

  const parsed = schema.safeParse(data);
  if (!parsed.success) {
    throw new ApiError("invalid_response", "Recibimos una respuesta inesperada del servidor.", response.status);
  }
  return parsed.data;
}
