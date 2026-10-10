"use client";

import { Check, Copy } from "lucide-react";
import { useEffect, useState } from "react";
import { cn } from "@/lib/utils/cn";

type CopyFieldProps = {
  value: string;
  copyLabel: string;
  copiedLabel: string;
  /** "code": fondo oscuro tipo terminal. */
  tone?: "light" | "code";
  className?: string;
};

/** Texto de una línea (URL, comando) con botón para copiarlo al portapapeles. */
export function CopyField({ value, copyLabel, copiedLabel, tone = "light", className }: CopyFieldProps) {
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (!copied) return;
    const timer = window.setTimeout(() => setCopied(false), 2000);
    return () => window.clearTimeout(timer);
  }, [copied]);

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(value);
      setCopied(true);
    } catch {
      // Portapapeles bloqueado: el texto queda visible para copiarlo a mano.
    }
  };

  return (
    <div
      className={cn(
        "flex w-full min-w-0 items-center gap-2 rounded-2xl p-1.5 pl-4 ring-1",
        tone === "code" ? "bg-slate-900 text-slate-100 ring-slate-800" : "bg-white/80 text-slate-800 ring-slate-200",
        className,
      )}
    >
      {/* Una línea que se desliza (no se corta ni estira el layout): el comando se ve completo. */}
      <code
        className="min-w-0 flex-1 overflow-x-auto font-mono text-sm whitespace-nowrap [scrollbar-width:none] [&::-webkit-scrollbar]:hidden"
        title={value}
      >
        {value}
      </code>
      <button
        type="button"
        onClick={copy}
        className={cn(
          "inline-flex h-9 shrink-0 items-center gap-1.5 rounded-xl px-3 text-xs font-semibold transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand",
          copied
            ? "bg-emerald-500 text-white"
            : tone === "code"
              ? "bg-white/10 text-white hover:bg-white/20"
              : "bg-brand text-white hover:bg-blue-700",
        )}
      >
        {copied ? <Check className="size-3.5" aria-hidden /> : <Copy className="size-3.5" aria-hidden />}
        <span aria-live="polite">{copied ? copiedLabel : copyLabel}</span>
      </button>
    </div>
  );
}
