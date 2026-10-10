import Image from "next/image";
import { site } from "@/content/site";
import { mascotReplaySrc } from "@/lib/utils/mascot";

type BrandLogoProps = {
  /** Reproduce la animación de entrada: la mascota cae y el nombre se revela. */
  intro?: boolean;
  /** Cambiarlo vuelve a reproducir el webp (caída + saludo). */
  replayKey?: number;
};

export function BrandLogo({ intro = false, replayKey }: BrandLogoProps) {
  const src = mascotReplaySrc(replayKey);

  return (
    <span className="flex items-center gap-2">
      {/*
        El webp (500x520) tiene mucho aire transparente. Esta caja mide lo que ocupa
        la mascota (365x348, desde x=67 y=153) y la imagen se desborda para encuadrarla,
        así el texto queda centrado con el cuerpo. La caída del webp se ve por encima.
        El webp ya trae la caída y el saludo; se reproduce una vez y queda en el último frame.
      */}
      <span className="relative aspect-365/348 h-10 shrink-0">
        <Image
          key={src}
          src={src}
          alt=""
          width={500}
          height={520}
          priority
          unoptimized
          className="absolute top-[-44%] left-[-18.4%] h-[149.4%] w-[137%] max-w-none"
        />
      </span>
      <span
        className={`font-display text-2xl font-semibold leading-none tracking-tight ${intro ? "animate-intro-name motion-reduce:animate-none" : ""}`}
      >
        {site.name}
      </span>
    </span>
  );
}
