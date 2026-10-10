import Image from "next/image";
import { LoadingMascot } from "@/components/ui/loading-mascot";
import { MASCOT_SRC } from "@/lib/utils/mascot";
import { cn } from "@/lib/utils/cn";
import { ClientIcon } from "./ClientIcon";

type ConnectionVisualProps = {
  clientName: string;
  /** "loading": la mascota de carga; "idle": la mascota de la marca. */
  mascot: "loading" | "idle";
  mascotAlt: string;
  className?: string;
};

/** El asistente de IA unido a StoreTalk por la misma línea animada que la conexión con Tiendanube. */
export function ConnectionVisual({ clientName, mascot, mascotAlt, className }: ConnectionVisualProps) {
  return (
    <div className={cn("flex items-center gap-2", className)}>
      <span
        aria-hidden
        className="grid size-14 shrink-0 place-items-center rounded-2xl bg-white text-slate-800 shadow-lg ring-1 ring-slate-200"
      >
        <ClientIcon name={clientName} />
      </span>
      <svg aria-hidden width="72" height="8" viewBox="0 0 72 8" className="shrink-0 text-brand">
        <line
          x1="4"
          y1="4"
          x2="68"
          y2="4"
          stroke="currentColor"
          strokeWidth="3"
          strokeLinecap="round"
          strokeDasharray="2 12"
          className="animate-dash motion-reduce:animate-none"
        />
      </svg>
      {mascot === "loading" ? (
        <LoadingMascot alt={mascotAlt} className="size-28 sm:size-28" />
      ) : (
        // 500x520; unoptimized para que Next no pierda la animación del webp.
        <Image src={MASCOT_SRC} alt={mascotAlt} width={500} height={520} unoptimized className="h-auto w-20 shrink-0" />
      )}
    </div>
  );
}
