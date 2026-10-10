/**
 * URL pública del servidor MCP que se pega en el asistente de IA.
 * En local apunta al túnel de ngrok; hosteado, al dominio del backend.
 */
export const MCP_URL = process.env.NEXT_PUBLIC_MCP_URL ?? "http://localhost:8000/mcp";
