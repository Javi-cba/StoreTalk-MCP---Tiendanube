import { cn } from "@/lib/utils/cn";

const variants = {
  primary:
    "bg-brand text-white shadow-lg shadow-blue-600/25 hover:bg-blue-700 active:bg-blue-800",
  glass: "glass text-slate-800 hover:bg-white/80",
  ghost: "text-slate-600 hover:bg-white/70 hover:text-slate-900",
  danger: "bg-rose-600 text-white shadow-lg shadow-rose-600/25 hover:bg-rose-700 active:bg-rose-800",
  "danger-ghost": "text-rose-600 hover:bg-rose-50 hover:text-rose-700",
} as const;

export type ButtonVariant = keyof typeof variants;

/** Clases compartidas por Button y ButtonLink, para que se vean idénticos. */
export function buttonStyles(variant: ButtonVariant, className?: string) {
  return cn(
    "inline-flex h-12 shrink-0 items-center justify-center gap-2 rounded-full px-6 text-sm whitespace-nowrap font-semibold transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand disabled:pointer-events-none disabled:opacity-60",
    variants[variant],
    className,
  );
}
