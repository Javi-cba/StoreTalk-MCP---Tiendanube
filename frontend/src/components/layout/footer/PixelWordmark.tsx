import { GLYPH_HEIGHT, pixelate } from "./pixelFont";

/** Cuántas filas de las letras se ven: el resto queda cortado por el borde del footer. */
const VISIBLE_ROWS = 4.6;
const CELL = 0.62;

type PixelWordmarkProps = {
  text: string;
};

export function PixelWordmark({ text }: PixelWordmarkProps) {
  const { cells, width } = pixelate(text);
  const inset = (1 - CELL) / 2;

  return (
    <svg
      aria-hidden
      viewBox={`0 0 ${width} ${Math.min(VISIBLE_ROWS, GLYPH_HEIGHT)}`}
      preserveAspectRatio="xMidYMin slice"
      className="block h-auto w-full"
    >
      <defs>
        <linearGradient id="pixel-fade" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2={width} y2="0">
          <stop offset="0" stopColor="rgb(37 99 235)" stopOpacity="0.75" />
          <stop offset="1" stopColor="rgb(14 165 233)" stopOpacity="0.6" />
        </linearGradient>
      </defs>
      <g fill="url(#pixel-fade)">
        {cells.map(({ x, y }) => (
          <rect key={`${x}-${y}`} x={x + inset} y={y + inset} width={CELL} height={CELL} rx={0.06} />
        ))}
      </g>
    </svg>
  );
}
