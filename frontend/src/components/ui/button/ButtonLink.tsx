import Link from "next/link";
import type { ComponentProps } from "react";
import { cn } from "@/lib/utils/cn";

const variants = {
  primary:
    "bg-brand text-white shadow-lg shadow-blue-600/25 hover:bg-blue-700 active:bg-blue-800",
  glass: "glass text-slate-800 hover:bg-white/80",
} as const;

type ButtonLinkProps = ComponentProps<typeof Link> & {
  variant?: keyof typeof variants;
};

export function ButtonLink({ variant = "primary", className, ...props }: ButtonLinkProps) {
  return (
    <Link
      className={cn(
        "inline-flex h-12 items-center justify-center gap-2 rounded-full px-6 text-sm font-semibold transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand",
        variants[variant],
        className,
      )}
      {...props}
    />
  );
}
