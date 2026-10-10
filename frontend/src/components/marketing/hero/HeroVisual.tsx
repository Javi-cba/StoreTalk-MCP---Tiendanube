import { StoreCard } from "./StoreCard";
import { UseCaseCube } from "./UseCaseCube";

/** Margen bajo la tarjeta para que no la pise cuando gira; en xl (hay margen de sobra) se corre a la derecha. */
const cubePosition = "absolute top-28 right-0 w-full sm:w-[74%] lg:w-[23rem] xl:-right-16";

/** Ilustración del hero: la tienda conectada enviando datos al cubo de casos de uso. */
export function HeroVisual() {
  return (
    <div className="relative mx-auto h-[670px] w-full max-w-xl">
      <div aria-hidden className="absolute inset-10 rounded-full bg-linear-to-tr from-sky-300/50 to-blue-400/30 blur-3xl" />

      {/*
        Conexión tienda → chat. El contenedor copia la posición del cubo y el SVG se pega a su borde
        izquierdo (right-full), así la línea termina justo en el chat en cualquier breakpoint en vez de
        verse a través del vidrio.
      */}
      <div aria-hidden className={`pointer-events-none hidden sm:block ${cubePosition}`}>
        <svg className="absolute right-full -top-12" width="80" height="160" fill="none">
          <path
            id="store-link"
            d="M20 14 C 20 100, 40 138, 80 138"
            stroke="url(#link)"
            strokeWidth="2.5"
            strokeDasharray="6 8"
            strokeLinecap="round"
            className="animate-dash motion-reduce:animate-none"
          />
          {/* Datos viajando de la tienda al chat. */}
          <g className="motion-reduce:hidden">
            {[0, 0.8, 1.6].map((delay) => (
              <circle key={delay} r="4" fill="#38bdf8" opacity="0">
                <animateMotion dur="2.4s" begin={`${delay}s`} repeatCount="indefinite">
                  <mpath href="#store-link" />
                </animateMotion>
                <animate
                  attributeName="opacity"
                  values="0;1;1;0"
                  keyTimes="0;0.15;0.8;1"
                  dur="2.4s"
                  begin={`${delay}s`}
                  repeatCount="indefinite"
                />
              </circle>
            ))}
          </g>
          <defs>
            <linearGradient id="link" x1="20" y1="14" x2="80" y2="138" gradientUnits="userSpaceOnUse">
              <stop stopColor="#2563eb" />
              <stop offset="1" stopColor="#38bdf8" />
            </linearGradient>
          </defs>
        </svg>
      </div>

      <UseCaseCube className={cubePosition} />

      <StoreCard className="absolute inset-x-0 top-2 sm:right-auto" />
    </div>
  );
}
