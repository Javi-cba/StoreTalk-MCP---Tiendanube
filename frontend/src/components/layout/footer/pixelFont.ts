/** Letras de 5x7 para la marca en cuadraditos del footer. "#" = cuadradito lleno. */
const glyphs: Record<string, string[]> = {
  A: [".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
  E: ["#####", "#....", "#....", "####.", "#....", "#....", "#####"],
  K: ["#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"],
  L: ["#....", "#....", "#....", "#....", "#....", "#....", "#####"],
  O: [".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
  R: ["####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"],
  S: [".####", "#....", "#....", ".###.", "....#", "....#", "####."],
  T: ["#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."],
};

export const GLYPH_WIDTH = 5;
export const GLYPH_HEIGHT = 7;
const LETTER_GAP = 1;

/** Devuelve las celdas llenas (x, y) de un texto y el ancho total en celdas. */
export function pixelate(text: string) {
  const cells: { x: number; y: number }[] = [];
  let offset = 0;

  for (const char of text.toUpperCase()) {
    const glyph = glyphs[char];
    if (glyph) {
      glyph.forEach((row, y) => {
        [...row].forEach((cell, x) => {
          if (cell === "#") cells.push({ x: offset + x, y });
        });
      });
    }
    offset += GLYPH_WIDTH + LETTER_GAP;
  }

  return { cells, width: offset - LETTER_GAP };
}
