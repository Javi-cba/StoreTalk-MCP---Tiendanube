import Link from "next/link";
import { ArrowRight } from "lucide-react";
import { BrandLogo } from "@/components/layout/brand-logo";
import { ButtonLink } from "@/components/ui/button";
import { navigation } from "@/content/site";
import { cn } from "@/lib/utils/cn";

const navLinkClass =
  "inline-flex h-10 items-center rounded-full px-4 text-sm font-medium text-slate-600 transition-colors hover:bg-white/70 hover:text-slate-900 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand";

export function Navbar() {
  return (
    <header className="pointer-events-none fixed inset-x-0 top-0 z-50 flex h-(--navbar-height) items-center px-4 sm:px-6">
      <nav className="relative isolate mx-auto grid h-16 w-full max-w-6xl grid-cols-[1fr_auto_1fr] items-center px-3">
        {/*
          Barra de vidrio: queda oculta durante el intro y se estira desde el centro cuando el logo llega.
          Más transparente y con bordes/sombra más suaves que el liquid-glass por defecto, para que se funda con la página.
        */}
        <span
          aria-hidden
          className="liquid-glass absolute inset-0 -z-10 rounded-full [--glass-backdrop:blur(16px)_saturate(140%)] [--glass-border:0.35] [--glass-bottom:0.06] [--glass-reflection:0.15] [--glass-shadow:inset_0_1px_1px_rgb(255_255_255/0.5),0_10px_30px_-18px_rgb(30_64_175/0.2)] [--glass-shine:0.25] [--glass-top:0.12] animate-intro-island motion-reduce:animate-none"
        />

        {/* Arranca grande en el centro de la pantalla y se acomoda en el navbar. */}
        <Link
          href="/"
          aria-label="Inicio"
          className="pointer-events-auto col-start-2 animate-intro-dock motion-reduce:animate-none"
        >
          <BrandLogo intro />
        </Link>

        <div className="pointer-events-auto hidden items-center justify-self-end gap-1 sm:flex animate-intro-content motion-reduce:animate-none">
          <Link href={navigation.signIn.href} className={cn(navLinkClass, "hidden lg:inline-flex")}>
            {navigation.signIn.label}
          </Link>
          <ButtonLink href={navigation.cta.href} className="h-10 whitespace-nowrap px-5">
            {navigation.cta.label}
            <ArrowRight className="size-4" />
          </ButtonLink>
        </div>
      </nav>
    </header>
  );
}
