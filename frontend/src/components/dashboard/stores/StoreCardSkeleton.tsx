import { GlassPanel } from "@/components/ui/glass";

const block = "rounded-md bg-slate-200/70";

/**
 * Placeholder de StoreCard con su misma estructura (paddings, alto de cada línea de texto, grilla de datos y
 * permisos), para que la altura no salte cuando llegan las tiendas.
 */
export function StoreCardSkeleton() {
  return (
    <GlassPanel aria-hidden className="grid animate-pulse gap-6 p-5 motion-reduce:animate-none sm:p-6 lg:grid-cols-[2fr_3fr] lg:gap-8">
      <div className="flex min-w-0 flex-col gap-4">
        <div className="flex items-center justify-between gap-2">
          <span className="h-6 w-24 rounded-full bg-slate-200/70" />
          <span className={`h-4 w-40 ${block}`} />
        </div>

        <div className="rounded-2xl bg-white/70 p-4 ring-1 ring-white sm:p-5">
          <div className="flex items-center gap-4">
            <span className="size-14 shrink-0 rounded-xl bg-slate-200/70" />
            <div className="flex flex-col">
              <span className={`h-6 w-32 ${block} my-0.5`} />
              <span className={`h-4 w-44 ${block} my-0.5`} />
            </div>
          </div>
          <div className="mt-4 grid grid-cols-2 gap-x-4 gap-y-3 border-t border-slate-200/70 pt-4 sm:grid-cols-3">
            {Array.from({ length: 6 }, (_, i) => (
              <div key={i} className="flex flex-col">
                <span className={`h-3 w-16 ${block} my-0.5`} />
                <span className={`h-4 w-24 ${block} my-0.5`} />
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="min-w-0">
        <span className={`mb-3 block h-4 w-36 ${block} my-0.5`} />
        <div className="grid gap-2 sm:grid-cols-2">
          {Array.from({ length: 8 }, (_, i) => (
            <span key={i} className="h-9 rounded-xl bg-white/80 ring-1 ring-slate-200" />
          ))}
        </div>
      </div>
    </GlassPanel>
  );
}
