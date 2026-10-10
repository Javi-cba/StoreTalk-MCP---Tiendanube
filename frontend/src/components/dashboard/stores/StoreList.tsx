"use client";

import { useRef, type ReactNode } from "react";
import { RotateCw, TriangleAlert } from "lucide-react";
import { Button } from "@/components/ui/button";
import { GlassPanel } from "@/components/ui/glass";
import { TiendanubeIcon } from "@/components/ui/icons";
import { Pagination } from "@/components/ui/pagination";
import { dashboardCopy } from "@/content/dashboard";
import { useStores } from "@/hooks/useStores";
import { cn } from "@/lib/utils/cn";
import { StoreCard } from "./StoreCard";
import { StoreCardSkeleton } from "./StoreCardSkeleton";

type StoreListProps = {
  /** Botón para conectar otra tienda (arriba a la derecha cuando ya hay tiendas). */
  headerAction: ReactNode;
  /** Botón para conectar la primera tienda (estado vacío). */
  emptyAction: ReactNode;
};

/** "Mis tiendas": encabezado + tarjetas paginadas por el backend, con estados de carga, error y vacío. */
export function StoreList({ headerAction, emptyAction }: StoreListProps) {
  const { state, page, pending, goToPage, retry, refresh } = useStores();
  const topRef = useRef<HTMLDivElement>(null);
  const copy = dashboardCopy;
  const data = state.status === "ready" ? state.data : null;
  const hasStores = data !== null && data.total > 0;

  const changePage = (next: number) => {
    goToPage(next);
    // Si el encabezado quedó arriba del viewport, se vuelve a él para ver la página nueva desde el principio.
    if (topRef.current && topRef.current.getBoundingClientRect().top < 0) {
      topRef.current.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  };

  return (
    <div ref={topRef} className="mx-auto screen-fill w-full max-w-6xl scroll-mt-(--navbar-height) px-4 pt-4 pb-10 sm:px-6">
      <header className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p className="text-xs font-semibold tracking-wider text-brand uppercase">{copy.eyebrow}</p>
          <h1 className="mt-1 text-2xl font-bold tracking-tight text-slate-900 sm:text-3xl">{copy.title}</h1>
          <p className="mt-1 max-w-xl text-slate-600">{copy.description}</p>
        </div>
        {hasStores && <div className="flex flex-col gap-3 sm:flex-row sm:items-start">{headerAction}</div>}
      </header>

      <div className="mt-6">
        {state.status === "loading" && (
          <div role="status" aria-label={copy.loadingLabel}>
            <StoreCardSkeleton />
          </div>
        )}

        {state.status === "error" && (
          <GlassPanel role="alert" className="flex flex-col items-center p-8 text-center">
            <TriangleAlert className="size-8 text-rose-500" aria-hidden />
            <h2 className="mt-3 text-lg font-semibold text-slate-900">{copy.error.title}</h2>
            <p className="mt-1 text-sm text-slate-600">{state.message}</p>
            <Button variant="glass" onClick={retry} className="mt-6">
              <RotateCw className="size-4" aria-hidden />
              {copy.error.retry}
            </Button>
          </GlassPanel>
        )}

        {data && !hasStores && (
          <GlassPanel className="mx-auto flex max-w-lg animate-rise-in flex-col items-center p-8 text-center motion-reduce:animate-none sm:p-10">
            <span className="grid size-14 place-items-center rounded-2xl bg-linear-to-br from-blue-600 to-sky-400 text-white shadow-lg shadow-blue-600/30">
              <TiendanubeIcon size={30} />
            </span>
            <h2 className="mt-5 text-xl font-bold tracking-tight text-slate-900">{copy.empty.title}</h2>
            <p className="mt-2 text-slate-600">{copy.empty.description}</p>
            <div className="mt-8 w-full sm:w-72">{emptyAction}</div>
          </GlassPanel>
        )}

        {data && hasStores && (
          <>
            {/* La página anterior queda atenuada hasta que llega la nueva: la altura no salta. */}
            <div
              key={data.page}
              aria-busy={pending}
              className={cn(
                "grid animate-rise-in gap-6 transition-opacity motion-reduce:animate-none",
                pending && "pointer-events-none opacity-50",
              )}
            >
              {data.stores.map((store) => (
                <StoreCard key={store.connection_id} store={store} onDisconnected={refresh} />
              ))}
            </div>

            {data.total_pages > 1 && (
              <div className="mt-6 flex flex-col items-center gap-3 sm:flex-row sm:justify-between">
                <p className="text-sm text-slate-500">
                  {copy.pagination.range(
                    (data.page - 1) * data.per_page + 1,
                    (data.page - 1) * data.per_page + data.stores.length,
                    data.total,
                  )}
                </p>
                <Pagination
                  page={pending ? page : data.page}
                  totalPages={data.total_pages}
                  onPageChange={changePage}
                  labels={copy.pagination}
                  disabled={pending}
                />
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
