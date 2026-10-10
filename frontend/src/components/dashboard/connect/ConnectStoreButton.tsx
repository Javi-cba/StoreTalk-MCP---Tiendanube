"use client";

import { ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useStartConnect } from "@/hooks/useStartConnect";
import { cn } from "@/lib/utils/cn";

type ConnectStoreButtonProps = {
  label: string;
  variant?: "primary" | "glass";
  className?: string;
};

/** Inicia el OAuth: pide la URL al backend con el JWT de Clerk y redirige a Tiendanube. */
export function ConnectStoreButton({ label, variant = "primary", className }: ConnectStoreButtonProps) {
  const { start, loading, error } = useStartConnect();

  return (
    <div className={cn("flex flex-col items-stretch gap-2", className)}>
      <Button variant={variant} loading={loading} onClick={start}>
        {label}
        {!loading && <ArrowRight className="size-4" aria-hidden />}
      </Button>
      {error && (
        <p role="alert" className="text-center text-sm text-rose-600">
          {error.message}
        </p>
      )}
    </div>
  );
}
