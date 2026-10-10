import Image from "next/image";
import { ArrowLeft } from "lucide-react";
import { ButtonLink } from "@/components/ui/button";
import { notFound } from "@/content/notFound";

/** 404: la mascota buscando en la caja (el webp ya trae el "404" y se repite en loop). */
export function NotFoundHero() {
  return (
    <section className="mx-auto flex w-full max-w-2xl flex-col items-center px-4 pt-4 pb-16 text-center sm:px-6">
      <div className="relative">
        <div aria-hidden className="absolute inset-8 rounded-full bg-linear-to-tr from-sky-300/50 to-blue-400/30 blur-3xl" />
        {/* 480x527; unoptimized para que Next no pierda la animación del webp. */}
        <Image
          src="/brand/mascot-404.webp"
          alt={notFound.imageAlt}
          width={480}
          height={527}
          priority
          unoptimized
          className="relative h-auto w-64 sm:w-80"
        />
      </div>

      <h1 className="mt-4 text-3xl font-bold tracking-tight text-balance text-slate-900 sm:text-4xl">
        {notFound.title}
      </h1>
      <p className="mt-4 max-w-md text-base leading-relaxed text-slate-600 sm:text-lg">{notFound.description}</p>

      <div className="mt-8 flex flex-wrap justify-center gap-3">
        <ButtonLink href={notFound.primaryCta.href}>
          <ArrowLeft className="size-4" />
          {notFound.primaryCta.label}
        </ButtonLink>
        <ButtonLink href={notFound.secondaryCta.href} variant="glass">
          {notFound.secondaryCta.label}
        </ButtonLink>
      </div>
    </section>
  );
}
