import { GlassPanel } from "@/components/ui/glass";
import { authorizeCopy } from "@/content/authorize";
import { ConnectionVisual } from "./ConnectionVisual";

/** Espera compacta mientras se valida el pedido (mismo estilo que "Conectando tu tienda…"). */
export function AuthorizeLoading({ clientName = "" }: { clientName?: string }) {
  const copy = authorizeCopy.loading;

  return (
    <GlassPanel
      role="status"
      aria-live="polite"
      className="flex w-full max-w-md animate-rise-in flex-col items-center p-8 text-center motion-reduce:animate-none"
    >
      <ConnectionVisual clientName={clientName} mascot="loading" mascotAlt={copy.mascotAlt} />
      <h1 className="mt-4 text-xl font-bold tracking-tight text-slate-900">{copy.title}</h1>
      <p className="mt-2 text-sm leading-relaxed text-slate-600">{copy.description}</p>
    </GlassPanel>
  );
}
