import Link from "next/link";
import type { ReactNode } from "react";
import { BrandLogo } from "@/components/layout/brand-logo";
import { cn } from "@/lib/utils/cn";
import { LogoOriginTracker } from "./LogoOriginTracker";
import { NavbarActions } from "./NavbarActions";

type NavbarProps = {
  /** Animación de entrada (logo grande que sube al navbar). Se apaga en páginas secundarias como la 404. */
  intro?: boolean;
  /** Reemplaza los links de la derecha (ej. el menú de cuenta en el área privada). */
  actions?: ReactNode;
};

export function Navbar({ intro = true, actions }: NavbarProps) {
  return (
    <header className="pointer-events-none fixed inset-x-0 top-0 z-50 flex h-(--navbar-height) items-center px-4 sm:px-6">
      <nav className="relative isolate mx-auto grid h-16 w-full max-w-6xl grid-cols-[1fr_auto_1fr] items-center px-3">
        {/*
          Barra de vidrio: queda oculta durante el intro y se estira desde el centro cuando el logo llega.
          Más transparente y con bordes/sombra más suaves que el liquid-glass por defecto, para que se funda con la página.
        */}
        <span
          aria-hidden
          className={cn(
            "liquid-glass absolute inset-0 -z-10 rounded-full [--glass-backdrop:blur(16px)_saturate(140%)] [--glass-border:0.35] [--glass-bottom:0.06] [--glass-reflection:0.15] [--glass-shadow:inset_0_1px_1px_rgb(255_255_255/0.5),0_10px_30px_-18px_rgb(30_64_175/0.2)] [--glass-shine:0.25] [--glass-top:0.12]",
            intro && "animate-intro-island motion-reduce:animate-none",
          )}
        />

        {/* Arranca grande en el centro de la pantalla y se acomoda en el navbar. */}
        <Link
          href="/"
          aria-label="Inicio"
          className={cn("pointer-events-auto col-start-2", intro && "animate-intro-dock motion-reduce:animate-none")}
        >
          {/* data-brand-logo: el login mide este nodo para animar el logo desde acá. */}
          <span data-brand-logo className="block">
            <BrandLogo intro={intro} />
          </span>
        </Link>

        <div
          className={cn(
            "pointer-events-auto items-center justify-self-end gap-1",
            // El menú de cuenta se ve siempre; los CTA de la landing, desde sm.
            actions ? "flex" : "hidden sm:flex",
            intro && "animate-intro-content motion-reduce:animate-none",
          )}
        >
          {actions ?? <NavbarActions />}
        </div>
      </nav>
      <LogoOriginTracker />
    </header>
  );
}
