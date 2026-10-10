import { Sparkles } from "lucide-react";
import { ClaudeIcon, CursorIcon, GeminiIcon, OpenAiIcon } from "@/components/ui/icons";

type ClientIconProps = {
  /** Nombre con el que se registró el asistente ("Claude", "ChatGPT"...). */
  name: string;
  size?: number;
};

/** Ícono del asistente de IA según su nombre; uno genérico si no lo conocemos. */
export function ClientIcon({ name, size = 28 }: ClientIconProps) {
  const client = name.toLowerCase();
  if (client.includes("claude")) return <ClaudeIcon size={size} />;
  if (client.includes("chatgpt") || client.includes("openai")) return <OpenAiIcon size={size} />;
  if (client.includes("gemini")) return <GeminiIcon size={size} />;
  if (client.includes("cursor")) return <CursorIcon size={size} />;
  return <Sparkles size={size} aria-hidden />;
}
