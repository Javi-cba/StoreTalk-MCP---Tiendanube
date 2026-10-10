"use client";

import { useEffect, useRef, useState } from "react";
import { heroUseCases } from "@/content/home";
import { cn } from "@/lib/utils/cn";
import { ClientSwitcher } from "./ClientSwitcher";
import { UseCaseFace } from "./UseCaseFace";

const FACES = 4;
const AUTOPLAY_MS = 5000;
const SWIPE_PX = 40;

const mod = (n: number, m: number) => ((n % m) + m) % m;

/**
 * Cara física → caso de uso. El cubo tiene 4 caras y hay más casos, así que cada cara muestra el
 * paso (step) que le toca entre `from` y `to`: así las caras visibles durante el giro no cambian
 * de contenido. La cara trasera (no visible) toma el siguiente paso.
 */
function caseIndexForFace(face: number, from: number, to: number) {
  const low = Math.min(from, to);
  const step = low + mod(face - low, FACES);
  return mod(step, heroUseCases.length);
}

/** Carrusel en forma de cubo 3D: cada cara es un caso de uso visto desde un cliente de IA distinto. */
export function UseCaseCube({ className }: { className?: string }) {
  const [{ from, to }, setMove] = useState({ from: 0, to: 0 });
  const [paused, setPaused] = useState(false);
  const touchStartX = useRef<number | null>(null);
  const total = heroUseCases.length;
  const active = mod(to, total);

  const moveBy = (delta: number) => setMove(({ to: current }) => ({ from: current, to: current + delta }));

  const goTo = (index: number) => {
    let delta = index - active;
    if (delta > total / 2) delta -= total;
    if (delta < -total / 2) delta += total;
    if (delta !== 0) moveBy(delta);
  };

  // Avanza solo y, como el paso nunca se resetea, después del último caso vuelve al primero.
  // Con "reducir movimiento" sigue avanzando, pero sin animación (motion-reduce en el cubo).
  useEffect(() => {
    if (paused) return;
    const id = setTimeout(() => moveBy(1), AUTOPLAY_MS);
    return () => clearTimeout(id);
  }, [to, paused]);

  return (
    <section
      aria-roledescription="carrusel"
      id="ejemplos"
      aria-label="Ejemplos de uso"
      className={cn("flex scroll-mt-28 flex-col gap-4", className)}
    >
      {/* cqw = ancho del contenedor: la profundidad del cubo es la mitad de su ancho. */}
      {/* Hover pausa el giro para poder leer; en touch se puede deslizar para pasar de caso. */}
      <div
        className="h-[30rem] touch-pan-y [container-type:inline-size] perspective-[1400px]"
        onMouseEnter={() => setPaused(true)}
        onMouseLeave={() => setPaused(false)}
        onTouchStart={(event) => (touchStartX.current = event.touches[0].clientX)}
        onTouchEnd={(event) => {
          if (touchStartX.current === null) return;
          const deltaX = event.changedTouches[0].clientX - touchStartX.current;
          touchStartX.current = null;
          if (Math.abs(deltaX) > SWIPE_PX) moveBy(deltaX < 0 ? 1 : -1);
        }}
      >
        <div
          className="relative size-full transform-3d transition-transform duration-900 ease-[cubic-bezier(0.65,0,0.35,1)] motion-reduce:transition-none"
          style={{ transform: `translateZ(-50cqw) rotateY(${-90 * to}deg)` }}
        >
          {Array.from({ length: FACES }, (_, face) => {
            const index = caseIndexForFace(face, from, to);
            const isFront = mod(to, FACES) === face;
            return (
              <div
                key={face}
                aria-hidden={!isFront}
                className="absolute inset-0 backface-hidden"
                style={{ transform: `rotateY(${90 * face}deg) translateZ(50cqw)` }}
              >
                <UseCaseFace useCase={heroUseCases[index]} />
              </div>
            );
          })}
        </div>
      </div>

      <ClientSwitcher active={active} onSelect={goTo} />
    </section>
  );
}
