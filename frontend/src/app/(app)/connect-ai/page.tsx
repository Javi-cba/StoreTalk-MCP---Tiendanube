import type { Metadata } from "next";
import { AssistantGuide } from "@/components/dashboard/assistant-guide";
import { assistantGuideCopy } from "@/content/assistantGuide";
import { site } from "@/content/site";

export const metadata: Metadata = { title: `${assistantGuideCopy.metaTitle} · ${site.name}` };

/** Guía pública: cómo agregar StoreTalk como conector en Claude, ChatGPT y otros clientes MCP. */
export default function ConnectAiPage() {
  return <AssistantGuide />;
}
