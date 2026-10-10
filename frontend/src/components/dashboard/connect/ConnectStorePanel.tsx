import { CircleCheck } from "lucide-react";
import { GlassPanel } from "@/components/ui/glass";
import { TiendanubeIcon } from "@/components/ui/icons";
import { connectCopy } from "@/content/connect";
import { ConnectStoreButton } from "./ConnectStoreButton";

/** Paso 1: el usuario ya está logueado y arranca la autorización en Tiendanube. */
export function ConnectStorePanel() {
  const copy = connectCopy.start;

  return (
    <GlassPanel className="w-full max-w-lg animate-rise-in p-6 motion-reduce:animate-none sm:p-8">
      <span className="grid size-14 place-items-center rounded-2xl bg-linear-to-br from-blue-600 to-sky-400 text-white shadow-lg shadow-blue-600/30">
        <TiendanubeIcon size={30} />
      </span>

      <p className="mt-6 text-xs font-semibold tracking-wider text-brand uppercase">{copy.eyebrow}</p>
      <h1 className="mt-2 text-2xl font-bold tracking-tight text-balance text-slate-900 sm:text-3xl">{copy.title}</h1>
      <p className="mt-3 leading-relaxed text-slate-600">{copy.description}</p>

      <ul className="mt-6 space-y-3">
        {copy.steps.map((step) => (
          <li key={step} className="flex items-start gap-3 text-sm text-slate-700">
            <CircleCheck className="mt-0.5 size-4 shrink-0 text-emerald-500" aria-hidden />
            {step}
          </li>
        ))}
      </ul>

      <ConnectStoreButton label={copy.cta} className="mt-8" />
    </GlassPanel>
  );
}
