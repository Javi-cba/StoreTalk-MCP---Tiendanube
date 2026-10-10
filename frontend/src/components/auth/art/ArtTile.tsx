import { TiendanubeIcon } from "@/components/ui/icons";
import { cn } from "@/lib/utils/cn";

export type ArtTileVariant =
  | "arch"
  | "bars"
  | "rings"
  | "cloud"
  | "chevrons"
  | "quarter"
  | "waves"
  | "plus"
  | "orbit";

const backgrounds: Record<ArtTileVariant, string> = {
  arch: "bg-blue-600",
  bars: "bg-blue-950",
  rings: "bg-sky-200",
  cloud: "bg-linear-to-br from-blue-500 to-sky-400",
  chevrons: "bg-indigo-500",
  quarter: "bg-white",
  waves: "bg-blue-950",
  plus: "bg-sky-400",
  orbit: "bg-blue-700",
};

/** Dibujo de cada pieza del mosaico (viewBox 200x160, se recorta para llenar la celda). */
function TileDrawing({ variant }: { variant: ArtTileVariant }) {
  switch (variant) {
    case "arch":
      return (
        <>
          <path d="M20 160V90a50 50 0 0 1 100 0v70z" fill="rgb(255 255 255 / 0.9)" />
          <path d="M100 160V90a50 50 0 0 1 100 0v70z" fill="rgb(186 230 253 / 0.55)" />
        </>
      );
    case "bars":
      return (
        <>
          <rect x="30" y="56" width="140" height="10" rx="5" fill="#38bdf8" />
          <rect x="30" y="76" width="110" height="10" rx="5" fill="#7dd3fc" opacity="0.7" />
          <rect x="30" y="96" width="70" height="10" rx="5" fill="#2563eb" />
          {[0, 1, 2, 3].map((row) =>
            [0, 1].map((col) => <circle key={`${row}-${col}`} cx={172 + col * 12} cy={22 + row * 12} r="2.5" fill="#60a5fa" />),
          )}
        </>
      );
    case "rings":
      return (
        <g fill="none" stroke="#2563eb" strokeWidth="3">
          {[16, 32, 48, 64].map((r) => (
            <circle key={r} cx="150" cy="40" r={r} opacity={1 - r / 90} />
          ))}
        </g>
      );
    case "chevrons":
      return (
        <g fill="rgb(255 255 255 / 0.75)">
          <path d="M60 70l40-40 40 40h-22l-18-18-18 18z" />
          <path d="M60 115l40-40 40 40h-22l-18-18-18 18z" opacity="0.6" />
        </g>
      );
    case "quarter":
      return (
        <>
          <path d="M0 160V40a120 120 0 0 1 120 120z" fill="#2563eb" />
          <circle cx="160" cy="44" r="14" fill="#38bdf8" />
        </>
      );
    case "waves":
      return (
        <g fill="none" stroke="#7dd3fc" strokeWidth="3" strokeLinecap="round">
          {[50, 72, 94, 116].map((y, i) => (
            <path
              key={y}
              d={`M-10 ${y}q20 -16 40 0t40 0 40 0 40 0 40 0 40 0`}
              opacity={1 - i * 0.2}
              strokeDasharray={i === 1 ? "4 10" : undefined}
              className={i === 1 ? "animate-dash motion-reduce:animate-none" : undefined}
            />
          ))}
        </g>
      );
    case "plus":
      return (
        <g fill="rgb(255 255 255 / 0.85)">
          {[0, 1, 2].map((row) =>
            [0, 1, 2, 3].map((col) => (
              <path key={`${row}-${col}`} d={`M${38 + col * 42} ${36 + row * 44}h4v-8h4v8h4v4h-4v8h-4v-8h-4z`} />
            )),
          )}
        </g>
      );
    case "orbit":
      return (
        <>
          <path d="M70 160a110 110 0 0 1 220 0z" fill="#172554" />
          <path d="M100 160a80 80 0 0 1 160 0" fill="none" stroke="#38bdf8" strokeWidth="2" />
          <circle cx="100" cy="160" r="9" fill="white" />
          {[0, 1, 2, 3].map((i) => (
            <rect key={i} x="0" y={30 + i * 14} width={150 - i * 25} height="5" rx="2.5" fill="rgb(255 255 255 / 0.25)" />
          ))}
        </>
      );
    case "cloud":
      return null;
  }
}

export function ArtTile({ variant, className }: { variant: ArtTileVariant; className?: string }) {
  return (
    <div className={cn("relative overflow-hidden", backgrounds[variant], className)}>
      {variant === "cloud" ? (
        <>
          {/* Pieza central: la marca de Tiendanube sobre un disco de vidrio. */}
          <div className="absolute top-1/2 left-1/2 size-56 -translate-1/2 rounded-full bg-white/20 ring-1 ring-white/40 backdrop-blur-sm" />
          <div className="absolute inset-0 grid place-items-center text-white animate-float motion-reduce:animate-none">
            <TiendanubeIcon size={150} />
          </div>
          <svg viewBox="0 0 24 24" className="absolute top-8 right-10 size-10 animate-[spin_14s_linear_infinite] fill-white motion-reduce:animate-none">
            <path d="M12 0l2.6 9.4L24 12l-9.4 2.6L12 24l-2.6-9.4L0 12l9.4-2.6z" />
          </svg>
          <svg viewBox="0 0 24 24" className="absolute bottom-10 left-12 size-5 fill-sky-100/80">
            <path d="M12 0l2.6 9.4L24 12l-9.4 2.6L12 24l-2.6-9.4L0 12l9.4-2.6z" />
          </svg>
        </>
      ) : (
        <svg viewBox="0 0 200 160" preserveAspectRatio="xMidYMid slice" className="absolute inset-0 size-full">
          <TileDrawing variant={variant} />
        </svg>
      )}
    </div>
  );
}
