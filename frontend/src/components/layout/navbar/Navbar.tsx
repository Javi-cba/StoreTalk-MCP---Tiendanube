import Link from "next/link";
import { BrandLogo } from "@/components/layout/brand-logo";

export function Navbar() {
  return (
    <header className="fixed inset-x-0 top-0 z-50 flex h-16 items-center justify-center">
      {/* Arranca grande en el centro de la pantalla y se acomoda en el navbar. */}
      <Link
        href="/"
        aria-label="Inicio"
        className="animate-intro-dock motion-reduce:animate-none"
      >
        <BrandLogo intro />
      </Link>
    </header>
  );
}
