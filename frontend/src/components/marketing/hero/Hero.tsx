import { GlassPanel } from "@/components/ui/glass";
import { TiendanubeIcon } from "@/components/ui/icons";
import { hero } from "@/content/home";
import { HeroPrimaryCta } from "./HeroPrimaryCta";
import { HeroVisual } from "./HeroVisual";

export function Hero() {
  return (
    <section className="mx-auto grid w-full max-w-6xl items-center gap-12 px-4 pt-2 pb-16 sm:px-6 grid-cols-1 lg:grid-cols-[minmax(0,1.1fr)_minmax(0,1fr)] lg:pt-4">
      <div>
        <GlassPanel className="inline-flex items-center gap-2 rounded-full px-4 py-2 text-sm font-medium text-slate-700">
          <TiendanubeIcon size={18} className="text-brand" />
          {hero.badge}
        </GlassPanel>

        <h1 className="mt-6 text-4xl font-bold tracking-tight text-balance text-slate-900 sm:text-5xl lg:text-[3.25rem] lg:leading-[1.1]">
          {hero.title}{" "}
          <span className="bg-linear-to-r lg:block from-blue-600 to-sky-500 bg-clip-text text-transparent">
            {hero.titleHighlight}
          </span>
        </h1>

        <div className="mt-8 h-px w-20 bg-slate-300" />

        <p className="mt-8 max-w-md text-lg leading-relaxed text-slate-600">{hero.description}</p>

        <div className="mt-8 flex flex-wrap gap-3">
          <HeroPrimaryCta />
        </div>

        <p className="mt-6 text-sm text-slate-500">{hero.compatibility}</p>
      </div>

      <HeroVisual />
    </section>
  );
}
