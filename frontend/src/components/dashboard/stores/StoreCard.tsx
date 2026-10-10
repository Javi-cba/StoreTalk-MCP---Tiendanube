import { CalendarDays, CircleAlert } from "lucide-react";
import { GlassPanel } from "@/components/ui/glass";
import { dashboardCopy } from "@/content/dashboard";
import type { ConnectedStore } from "@/lib/schemas/stores";
import { cn } from "@/lib/utils/cn";
import { formatDate } from "@/lib/utils/format";
import { DisconnectStoreButton } from "./DisconnectStoreButton";
import { ScopeList } from "./ScopeList";
import { StoreSummary } from "./StoreSummary";

/** Una tienda conectada a todo el ancho: estado y datos a la izquierda, permisos a la derecha (desde lg). */
type StoreCardProps = {
  store: ConnectedStore;
  onDisconnected: (connectionId: string) => void;
};

export function StoreCard({ store, onDisconnected }: StoreCardProps) {
  const copy = dashboardCopy.card;
  const active = store.status === "active";

  return (
    <GlassPanel className="grid gap-6 p-5 sm:p-6 lg:grid-cols-[2fr_3fr] lg:gap-8">
      <div className="flex min-w-0 flex-col gap-4">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <span
            className={cn(
              "inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-semibold ring-1",
              active ? "bg-emerald-50 text-emerald-700 ring-emerald-100" : "bg-amber-50 text-amber-700 ring-amber-100",
            )}
          >
            <span className={cn("size-1.5 rounded-full", active ? "bg-emerald-500" : "bg-amber-500")} />
            {copy.status[store.status]}
          </span>
          <span className="inline-flex items-center gap-1.5 text-xs text-slate-500">
            <CalendarDays className="size-3.5" aria-hidden />
            {copy.connectedAt} {formatDate(store.connected_at)}
          </span>
        </div>

        <StoreSummary store={store} />

        {!active && (
          <p className="flex items-start gap-2 text-sm text-amber-700">
            <CircleAlert className="mt-0.5 size-4 shrink-0" aria-hidden />
            {copy.unavailableHint}
          </p>
        )}
      </div>

      <section aria-label={copy.scopesTitle} className="min-w-0">
        <h3 className="mb-3 text-sm font-semibold text-slate-900">{copy.scopesTitle}</h3>
        <ScopeList scopes={store.scopes} emptyLabel={copy.noScopes} />
      </section>

      {/* Acción destructiva abajo a la derecha, separada del contenido. */}
      <footer className="flex justify-end border-t border-slate-200/70 pt-4 lg:col-span-2">
        <DisconnectStoreButton
          connectionId={store.connection_id}
          storeName={store.name ?? `#${store.store_id}`}
          onDisconnected={onDisconnected}
        />
      </footer>
    </GlassPanel>
  );
}
