import { ChevronLeft, ChevronRight, ChevronsLeft, ChevronsRight, Ellipsis, type LucideIcon } from "lucide-react";
import { getPageItems } from "@/lib/utils/pagination";
import { cn } from "@/lib/utils/cn";

export type PaginationLabels = {
  nav: string;
  first: string;
  previous: string;
  next: string;
  last: string;
  /** Ej. (3) => "Página 3". */
  page: (page: number) => string;
};

type PaginationProps = {
  page: number;
  totalPages: number;
  onPageChange: (page: number) => void;
  labels: PaginationLabels;
  /** Mientras carga una página, se bloquea para no encolar pedidos. */
  disabled?: boolean;
  className?: string;
};

const itemClass =
  "grid size-10 place-items-center rounded-full text-sm font-semibold transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand disabled:pointer-events-none";

/** Paginador en una píldora de vidrio: primera/anterior, números con "…", siguiente/última. */
export function Pagination({ page, totalPages, onPageChange, labels, disabled, className }: PaginationProps) {
  if (totalPages <= 1) return null;

  const atStart = page <= 1;
  const atEnd = page >= totalPages;

  return (
    <nav aria-label={labels.nav} className={cn("glass inline-flex items-center gap-0.5 rounded-full p-1", className)}>
      <ArrowButton icon={ChevronsLeft} label={labels.first} disabled={disabled || atStart} onClick={() => onPageChange(1)} className="hidden sm:grid" />
      <ArrowButton icon={ChevronLeft} label={labels.previous} disabled={disabled || atStart} onClick={() => onPageChange(page - 1)} />

      <ul className="flex items-center gap-0.5">
        {getPageItems(page, totalPages).map((item) =>
          item.type === "gap" ? (
            <li key={item.key} aria-hidden className="grid size-10 place-items-center text-slate-400">
              <Ellipsis className="size-4" />
            </li>
          ) : (
            <li key={item.page}>
              <button
                type="button"
                aria-label={labels.page(item.page)}
                aria-current={item.page === page ? "page" : undefined}
                disabled={disabled && item.page !== page}
                onClick={() => item.page !== page && onPageChange(item.page)}
                className={cn(
                  itemClass,
                  item.page === page
                    ? "bg-brand text-white shadow-md shadow-blue-600/30"
                    : "text-slate-600 hover:bg-white/80 hover:text-slate-900 disabled:opacity-50",
                )}
              >
                {item.page}
              </button>
            </li>
          ),
        )}
      </ul>

      <ArrowButton icon={ChevronRight} label={labels.next} disabled={disabled || atEnd} onClick={() => onPageChange(page + 1)} />
      <ArrowButton icon={ChevronsRight} label={labels.last} disabled={disabled || atEnd} onClick={() => onPageChange(totalPages)} className="hidden sm:grid" />
    </nav>
  );
}

type ArrowButtonProps = {
  icon: LucideIcon;
  label: string;
  disabled?: boolean;
  onClick: () => void;
  className?: string;
};

function ArrowButton({ icon: Icon, label, disabled, onClick, className }: ArrowButtonProps) {
  return (
    <button
      type="button"
      aria-label={label}
      title={label}
      disabled={disabled}
      onClick={onClick}
      className={cn(itemClass, "text-slate-600 hover:bg-white/80 hover:text-brand disabled:opacity-35", className)}
    >
      <Icon className="size-4.5" aria-hidden />
    </button>
  );
}
