import { ExternalLink } from "lucide-react";
import { TiendanubeIcon } from "@/components/ui/icons";
import { connectCopy } from "@/content/connect";
import type { ConnectedStore } from "@/lib/schemas/stores";
import { formatCountry, formatHost, formatLanguage } from "@/lib/utils/format";

/** Tarjeta con la identidad de la tienda (logo, nombre, dominio) y sus datos básicos. */
export function StoreSummary({ store }: { store: ConnectedStore }) {
  const copy = connectCopy;
  const host = formatHost(store.url ?? store.domain);
  const details: { label: string; value: string | null }[] = [
    { label: copy.details.storeId, value: String(store.store_id) },
    { label: copy.details.email, value: store.email },
    { label: copy.details.country, value: formatCountry(store.country) },
    { label: copy.details.language, value: formatLanguage(store.language) },
    { label: copy.details.currency, value: store.currency },
    { label: copy.details.plan, value: store.plan },
  ];
  const visibleDetails = details.filter((detail) => detail.value);

  return (
    <div className="rounded-2xl bg-white/70 p-4 ring-1 ring-white sm:p-5">
      <div className="flex items-center gap-4">
        {store.logo_url ? (
          // Logo alojado en el CDN de Tiendanube (dominio variable): <img> evita configurar remotePatterns.
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={store.logo_url}
            alt=""
            className="size-14 shrink-0 rounded-xl bg-white object-contain p-1 shadow-sm ring-1 ring-slate-200"
          />
        ) : (
          <span className="grid size-14 shrink-0 place-items-center rounded-xl bg-linear-to-br from-blue-600 to-sky-400 text-white shadow-lg shadow-blue-600/30">
            <TiendanubeIcon size={28} />
          </span>
        )}
        <div className="min-w-0">
          <p className="truncate text-lg font-semibold text-slate-900">
            {store.name ?? copy.success.fallbackStoreName}
          </p>
          {host && store.url ? (
            <a
              href={store.url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex max-w-full items-center gap-1 text-sm font-medium text-brand hover:underline"
            >
              <span className="truncate">{host}</span>
              <ExternalLink className="size-3.5 shrink-0" aria-hidden />
              <span className="sr-only">({copy.success.visitStore})</span>
            </a>
          ) : (
            host && <p className="truncate text-sm text-slate-500">{host}</p>
          )}
        </div>
      </div>

      {visibleDetails.length > 0 && (
        <dl className="mt-4 grid grid-cols-2 gap-x-4 gap-y-3 border-t border-slate-200/70 pt-4 sm:grid-cols-3">
          {visibleDetails.map((detail) => (
            <div key={detail.label} className="min-w-0">
              <dt className="text-xs text-slate-500">{detail.label}</dt>
              <dd className="truncate text-sm font-medium text-slate-900" title={detail.value ?? undefined}>
                {detail.value}
              </dd>
            </div>
          ))}
        </dl>
      )}
    </div>
  );
}
