import Image from "next/image";
import { MASCOT_LOADING_SRC } from "@/lib/utils/mascot";
import { cn } from "@/lib/utils/cn";

type LoadingMascotProps = {
  alt: string;
  className?: string;
};

/** Mascota animada de "cargando" con su resplandor; reemplaza a los spinners en pantallas de espera. */
export function LoadingMascot({ alt, className }: LoadingMascotProps) {
  return (
    <div className={cn("relative size-48 sm:size-56", className)}>
      <div aria-hidden className="absolute inset-8 rounded-full bg-linear-to-tr from-sky-300/50 to-blue-400/30 blur-3xl" />
      {/* 320x320; unoptimized para que Next no pierda la animación del webp. */}
      <Image src={MASCOT_LOADING_SRC} alt={alt} width={320} height={320} priority unoptimized className="relative size-full" />
    </div>
  );
}
