import { Wrench } from "lucide-react";
import type { UseCase, UseCaseTone } from "@/content/home";
import { cn } from "@/lib/utils/cn";

const toneClasses: Record<UseCaseTone, string> = {
  danger: "bg-rose-50 text-rose-600",
  success: "bg-emerald-50 text-emerald-600",
  info: "bg-blue-50 text-blue-700",
  neutral: "bg-slate-100 text-slate-600",
};

/**
 * Una cara del cubo: conversación de ejemplo desde un cliente de IA, en vidrio líquido con el
 * mismo tinte celeste/índigo que el fondo de la página.
 */
export function UseCaseFace({ useCase }: { useCase: UseCase }) {
  const { client, icon: Icon, category, question, answer, rows, tool } = useCase;
  const ClientIcon = client.icon;

  return (
    <div className="liquid-glass relative flex size-full flex-col rounded-3xl p-5">
      <div
        aria-hidden
        className="absolute inset-0 -z-10 rounded-[inherit] bg-linear-to-br from-sky-200/40 via-white/10 to-indigo-200/40"
      />
      <div className="flex items-center gap-2 border-b border-white/70 pb-3">
        <span className={cn("grid size-8 place-items-center rounded-xl bg-white shadow-sm", client.color)}>
          <ClientIcon size={18} />
        </span>
        <span className="text-sm font-semibold text-slate-800">{client.name}</span>
        <span className="ml-auto inline-flex items-center gap-1.5 rounded-full bg-white px-2.5 py-1 text-xs font-medium text-slate-600 shadow-sm">
          <Icon className="size-3.5 text-brand" />
          {category}
        </span>
      </div>

      <p className="mt-4 ml-auto w-fit max-w-[85%] rounded-2xl rounded-br-md bg-brand px-4 py-2.5 text-sm text-white shadow-md shadow-blue-600/20">
        {question}
      </p>

      <div className="mt-3 rounded-2xl sm:max-w-[92%] rounded-bl-md bg-white/75 p-4 pb-5 text-sm text-slate-700 shadow-sm">
        <p>{answer}</p>
        <ul className="mt-3 space-y-3">
          {rows.map((row) => (
            <li key={row.label} className="flex items-center justify-between gap-3">
              {/* En mobile el detalle baja a otra línea para no cortarse. */}
              <span className="min-w-0 sm:truncate">
                <span className="font-medium text-slate-900">{row.label}</span>
                {row.detail && (
                  <span className="block text-slate-500 sm:inline">
                    <span className="hidden sm:inline"> · </span>
                    {row.detail}
                  </span>
                )}
              </span>
              {row.badge && (
                <span
                  className={cn(
                    "shrink-0 rounded-full px-2 py-0.5 text-xs font-medium",
                    toneClasses[row.tone ?? "neutral"],
                  )}
                >
                  {row.badge}
                </span>
              )}
            </li>
          ))}
        </ul>
      </div>

      <div className="mt-auto pt-3">
        <span className="inline-flex items-center gap-1.5 rounded-full bg-blue-50/80 px-3 py-1 font-mono text-xs text-blue-700">
          <Wrench className="size-3" />
          {tool}
        </span>
      </div>
    </div>
  );
}
