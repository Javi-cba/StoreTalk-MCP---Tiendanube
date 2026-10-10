import Image from "next/image";
import { Check, Home, Store } from "lucide-react";
import { ButtonLink } from "@/components/ui/button";
import { GlassPanel } from "@/components/ui/glass";
import { connectCopy } from "@/content/connect";
import type { ConnectedStore } from "@/lib/schemas/stores";
import { ScopeList, StoreSummary } from "@/components/dashboard/stores";

/** Panel ancho que llena la pantalla: festejo y acciones a la izquierda, datos de la tienda a la derecha. */
export function ConnectSuccess({ store }: { store: ConnectedStore }) {
  const copy = connectCopy.success;

  return (
    <GlassPanel className="grid w-full flex-1 animate-rise-in items-center gap-8 p-6 motion-reduce:animate-none sm:p-8 lg:grid-cols-[2fr_3fr] lg:gap-12 lg:p-12">
      <div className="flex flex-col items-center text-center lg:items-start lg:text-left">
        <div className="relative">
          <div aria-hidden className="absolute inset-6 rounded-full bg-linear-to-tr from-emerald-300/40 to-sky-300/40 blur-2xl" />
          {/* 480x534; unoptimized para que Next no pierda la animación del webp. */}
          <Image
            src="/brand/mascot-celebrate.webp"
            alt={copy.mascotAlt}
            width={480}
            height={534}
            priority
            unoptimized
            className="relative h-auto w-36 sm:w-44"
          />
          <span className="absolute right-0 bottom-3 grid size-10 animate-pop-in place-items-center rounded-full bg-emerald-500 text-white shadow-lg shadow-emerald-500/30 ring-4 ring-white motion-reduce:animate-none">
            <Check className="size-5" strokeWidth={3} aria-hidden />
          </span>
        </div>
        <p className="mt-4 text-xs font-semibold tracking-wider text-emerald-600 uppercase">{copy.eyebrow}</p>
        <h1 className="mt-2 text-2xl font-bold tracking-tight text-balance text-slate-900 sm:text-3xl lg:text-4xl">
          {copy.title}
        </h1>
        <p className="mt-3 max-w-md leading-relaxed text-slate-600">{copy.description}</p>

        {/* Dos acciones principales en fila y "Volver al inicio" centrado debajo, como secundario. */}
        <div className="mt-8 grid w-full gap-3 sm:w-fit sm:grid-cols-2">
          <ButtonLink href="/dashboard">
            <Store className="size-4" aria-hidden />
            {copy.myStores}
          </ButtonLink>
          <ButtonLink href="/connect" variant="glass">
            {copy.connectAnother}
          </ButtonLink>
          <ButtonLink href="/" variant="glass" className="w-full sm:col-span-2 sm:w-auto sm:justify-self-center">
            <Home className="size-4" aria-hidden />
            {copy.home}
          </ButtonLink>
        </div>
      </div>

      <div className="flex min-w-0 flex-col gap-6">
        <section aria-label={copy.detailsTitle}>
          <StoreSummary store={store} />
        </section>

        <section aria-labelledby="granted-scopes">
          <h2 id="granted-scopes" className="text-sm font-semibold text-slate-900">
            {copy.scopesTitle}
          </h2>
          <p className="mt-1 mb-3 text-sm text-slate-500">{copy.scopesDescription}</p>
          <ScopeList scopes={store.scopes} emptyLabel={copy.noScopes} />
        </section>
      </div>
    </GlassPanel>
  );
}
