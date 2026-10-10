import { AuthorCredit } from "@/components/layout/author-credit";
import { ArtTile } from "./ArtTile";

/** Mosaico geométrico con la paleta de la marca (azules, celestes y blanco), solo decorativo. */
export function AuthArt() {
  return (
    <div className="relative h-full min-h-[40rem] overflow-hidden rounded-[2rem] shadow-[0_24px_60px_-30px_rgb(30_64_175/0.55)]">
      <div className="grid h-full grid-cols-3 grid-rows-4">
        <ArtTile variant="arch" />
        <ArtTile variant="bars" />
        <ArtTile variant="rings" />
        <ArtTile variant="cloud" className="col-span-2 row-span-2" />
        <ArtTile variant="chevrons" />
        <ArtTile variant="plus" />
        <ArtTile variant="quarter" />
        <ArtTile variant="orbit" className="col-span-1" />
        <ArtTile variant="waves" />
      </div>

      {/* Brillo general para que el mosaico se funda con el vidrio del resto de la web. */}
      <div className="pointer-events-none absolute inset-0 bg-linear-to-tr from-blue-950/20 via-transparent to-white/15" />

      <div className="liquid-glass absolute bottom-6 left-6 rounded-full px-4 py-2">
        <AuthorCredit />
      </div>
    </div>
  );
}
