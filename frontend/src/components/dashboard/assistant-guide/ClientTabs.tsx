import { Sparkles, SquareTerminal } from "lucide-react";
import { ClaudeIcon, OpenAiIcon } from "@/components/ui/icons";
import type { AssistantClientId } from "@/content/assistantGuide";
import { cn } from "@/lib/utils/cn";

type ClientTabsProps = {
  clients: readonly { id: AssistantClientId; label: string }[];
  active: AssistantClientId;
  onChange: (id: AssistantClientId) => void;
  label: string;
};

function TabIcon({ id }: { id: AssistantClientId }) {
  if (id === "claude") return <ClaudeIcon size={16} className="shrink-0" />;
  if (id === "claude-code") return <SquareTerminal className="size-4 shrink-0" aria-hidden />;
  if (id === "chatgpt") return <OpenAiIcon size={16} className="shrink-0" />;
  return <Sparkles className="size-4 shrink-0" aria-hidden />;
}

/** Selector de asistente en una píldora de vidrio (mismo lenguaje visual que el paginado). */
export function ClientTabs({ clients, active, onChange, label }: ClientTabsProps) {
  return (
    <div role="tablist" aria-label={label} className="glass grid w-full grid-cols-2 gap-1 rounded-3xl p-1 sm:grid-cols-4 sm:rounded-full">
      {clients.map((client) => (
        <button
          key={client.id}
          type="button"
          role="tab"
          id={`tab-${client.id}`}
          aria-selected={client.id === active}
          aria-controls={`panel-${client.id}`}
          onClick={() => onChange(client.id)}
          className={cn(
            "inline-flex h-10 items-center justify-center gap-2 rounded-full px-3 text-sm font-semibold whitespace-nowrap transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand",
            client.id === active
              ? "bg-brand text-white shadow-md shadow-blue-600/30"
              : "text-slate-600 hover:bg-white/80 hover:text-slate-900",
          )}
        >
          <TabIcon id={client.id} />
          {client.label}
        </button>
      ))}
    </div>
  );
}
