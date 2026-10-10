import Link from "next/link";
import { Globe } from "lucide-react";
import { BrandLogo } from "@/components/layout/brand-logo";
import { LinkedinIcon } from "@/components/ui/icons";
import { footer, site } from "@/content/site";
import { PixelWordmark } from "./PixelWordmark";

const authorLinkClass =
  "inline-flex items-center gap-1.5 text-sm font-medium text-slate-600 underline-offset-4 transition-colors hover:text-brand hover:underline";

export function Footer() {
  return (
    <footer className="liquid-glass relative mt-auto overflow-hidden rounded-t-2xl">
      {/* Luces difusas en los celestes de la página, vistas a través del vidrio. */}
      <div aria-hidden className="absolute -top-40 right-[-5%] -z-10 size-[36rem] rounded-full bg-sky-300/40 blur-3xl" />
      <div aria-hidden className="absolute -bottom-40 -left-32 -z-10 size-[32rem] rounded-full bg-blue-300/35 blur-3xl" />
      <div aria-hidden className="bg-grain absolute inset-0 -z-10 opacity-15 mix-blend-soft-light" />

      <div className="mx-auto grid w-full max-w-6xl gap-10 px-4 pt-14 pb-10 sm:px-6 md:grid-cols-[1fr_auto]">
        <div className="max-w-xs">
          <Link href="/" aria-label="Inicio" className="inline-block">
            <BrandLogo />
          </Link>
          <p className="mt-4 text-sm leading-relaxed text-slate-600">{footer.tagline}</p>
        </div>

        <nav className="flex gap-16">
          {footer.columns.map((column) => (
            <div key={column.title}>
              <p className="text-xs font-medium tracking-[0.15em] text-slate-500 uppercase">{column.title}</p>
              <ul className="mt-4 space-y-2.5">
                {column.links.map((link) => (
                  <li key={link.label}>
                    <Link href={link.href} className="text-sm font-medium text-slate-700 transition-colors hover:text-brand">
                      {link.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </nav>

        <div className="flex flex-col gap-3 text-xs text-slate-500 sm:flex-row sm:items-center sm:justify-between md:col-span-2">
          <p>© {site.name}</p>
          <p className="flex flex-wrap items-center gap-x-5 gap-y-2">
            <span className="mr-1 text-sm text-slate-600">
              {footer.author.prefix}{" "}
              <span className="bg-linear-to-r from-blue-600 to-sky-500 bg-clip-text text-base font-semibold text-transparent">
                {footer.author.name}
              </span>
            </span>
            <a href={footer.author.portfolio.href} target="_blank" rel="noopener noreferrer" className={authorLinkClass}>
              <Globe className="size-4" />
              {footer.author.portfolio.label}
            </a>
            <a href={footer.author.linkedin.href} target="_blank" rel="noopener noreferrer" className={authorLinkClass}>
              <LinkedinIcon size={14} />
              {footer.author.linkedin.label}
            </a>
          </p>
        </div>
      </div>

      <PixelWordmark text={site.name} />
    </footer>
  );
}
