import { TiendanubeIcon } from "@/components/ui/icons";
import { heroStore } from "@/content/home";
import { cn } from "@/lib/utils/cn";

/** Tarjeta horizontal de la tienda conectada, arriba del cubo: flota con un leve balanceo y muestra que está en vivo. */
export function StoreCard({ className }: { className?: string }) {
  return (
    <div
      aria-hidden
      className={cn(
        "liquid-glass relative flex items-center gap-3 rounded-2xl p-3 animate-float-tilt motion-reduce:animate-none sm:w-72",
        className,
      )}
    >
      <span className="relative grid size-11 shrink-0 place-items-center rounded-xl bg-linear-to-br from-blue-600 to-sky-400 text-white shadow-lg shadow-blue-600/30">
        <TiendanubeIcon size={24} />
        <span className="absolute -top-1 -right-1 flex size-3">
          <span className="absolute inline-flex size-full animate-ping rounded-full bg-emerald-400 opacity-75 motion-reduce:animate-none" />
          <span className="relative inline-flex size-3 rounded-full border-2 border-white bg-emerald-500" />
        </span>
      </span>

      <span className="block">
        <span className="block text-sm font-semibold text-slate-900">{heroStore.name}</span>
        <span className="flex items-center gap-1.5 text-xs font-medium text-emerald-600">
          <span className="size-1.5 rounded-full bg-emerald-500" />
          {heroStore.status}
        </span>
      </span>

      <div className="ml-auto space-y-1 border-l border-white/70 pl-3">
        {heroStore.stats.map((stat) => (
          <span key={stat.label} className="flex items-baseline justify-between gap-3 text-xs">
            <span className="text-slate-500">{stat.label}</span>
            <span className="font-semibold text-slate-900">{stat.value}</span>
          </span>
        ))}
      </div>
    </div>
  );
}
