import { GlassPanel } from "@/components/ui/glass";
import { TiendanubeIcon } from "@/components/ui/icons";
import { LoadingMascot } from "@/components/ui/loading-mascot";
import { connectCopy } from "@/content/connect";

/** Mientras se canjea el code: Tiendanube unida a la mascota de StoreTalk (cargando) por una línea animada. */
export function CallbackLoading() {
  const copy = connectCopy.callback;

  return (
    <GlassPanel
      role="status"
      aria-live="polite"
      className="flex w-full max-w-md animate-rise-in flex-col items-center p-8 text-center motion-reduce:animate-none"
    >
      <div className="flex items-center gap-2">
        <span
          aria-hidden
          className="grid size-14 shrink-0 place-items-center rounded-2xl bg-linear-to-br from-blue-600 to-sky-400 text-white shadow-lg shadow-blue-600/30"
        >
          <TiendanubeIcon size={28} />
        </span>
        <svg aria-hidden width="72" height="8" viewBox="0 0 72 8" className="shrink-0 text-brand">
          <line
            x1="4"
            y1="4"
            x2="68"
            y2="4"
            stroke="currentColor"
            strokeWidth="3"
            strokeLinecap="round"
            strokeDasharray="2 12"
            className="animate-dash motion-reduce:animate-none"
          />
        </svg>
        <LoadingMascot alt={copy.mascotAlt} className="size-28 sm:size-28" />
      </div>

      <h1 className="mt-4 text-xl font-bold tracking-tight text-slate-900">{copy.loadingTitle}</h1>
      <p className="mt-2 text-sm leading-relaxed text-slate-600">{copy.loadingDescription}</p>
    </GlassPanel>
  );
}
