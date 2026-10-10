import type { ComponentProps } from "react";
import { cn } from "@/lib/utils/cn";

export function GlassPanel({ className, ...props }: ComponentProps<"div">) {
  return <div className={cn("glass rounded-3xl", className)} {...props} />;
}
