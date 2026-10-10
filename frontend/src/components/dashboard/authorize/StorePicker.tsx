import { Check } from "lucide-react";
import { TiendanubeIcon } from "@/components/ui/icons";
import { authorizeCopy } from "@/content/authorize";
import type { ConsentStore } from "@/lib/schemas/oauth";
import { cn } from "@/lib/utils/cn";

type StorePickerProps = {
  stores: ConsentStore[];
  selected: string | null;
  onSelect: (connectionId: string) => void;
  disabled?: boolean;
};

/** Tiendas del usuario como opciones de radio: se comparte una sola con el asistente. */
export function StorePicker({ stores, selected, onSelect, disabled }: StorePickerProps) {
  const copy = authorizeCopy.consent;

  return (
    <fieldset disabled={disabled} className="min-w-0">
      <legend className="mb-3 text-sm font-semibold text-slate-900">{copy.storesTitle}</legend>
      <div className="flex max-h-72 flex-col gap-2 overflow-y-auto p-0.5">
        {stores.map((store) => {
          const active = store.connection_id === selected;
          return (
            <label
              key={store.connection_id}
              className={cn(
                "flex cursor-pointer items-center gap-3 rounded-2xl bg-white/80 p-3 ring-1 transition-all",
                active ? "shadow-md shadow-blue-600/10 ring-2 ring-brand" : "ring-slate-200 hover:ring-blue-300",
              )}
            >
              <input
                type="radio"
                name="store"
                value={store.connection_id}
                checked={active}
                onChange={() => onSelect(store.connection_id)}
                className="sr-only"
              />
              <span className="grid size-11 shrink-0 place-items-center rounded-xl bg-linear-to-br from-blue-600 to-sky-400 text-white shadow-md shadow-blue-600/25">
                <TiendanubeIcon size={22} />
              </span>
              <span className="min-w-0 flex-1">
                <span className="block truncate font-semibold text-slate-900">{store.name ?? copy.fallbackStoreName}</span>
                <span className="block text-xs text-slate-500">
                  {copy.storeId} {store.store_id} · {copy.permissions(store.scopes.length)}
                </span>
              </span>
              <span
                aria-hidden
                className={cn(
                  "grid size-6 shrink-0 place-items-center rounded-full ring-1 transition-colors",
                  active ? "bg-brand text-white ring-brand" : "bg-white text-transparent ring-slate-300",
                )}
              >
                <Check className="size-3.5" strokeWidth={3} />
              </span>
            </label>
          );
        })}
      </div>
    </fieldset>
  );
}
