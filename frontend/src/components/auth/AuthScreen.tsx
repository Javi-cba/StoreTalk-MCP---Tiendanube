"use client";

import Link from "next/link";
import { Suspense, useRef, type ReactNode } from "react";
import { ArrowLeft, ShieldCheck } from "lucide-react";
import { BrandLogo } from "@/components/layout/brand-logo";
import { authCopy, type AuthFlow } from "@/content/auth";
import { introCardClass, introRevealClass, useAuthIntro } from "@/hooks/useAuthIntro";
import { cn } from "@/lib/utils/cn";
import { OAuthButtons } from "./OAuthButtons";

type AuthScreenProps = {
  flow: AuthFlow;
  /** Panel decorativo de la derecha (Server Component). */
  art: ReactNode;
};

/** Login / registro a pantalla completa: formulario a la izquierda y arte de marca a la derecha. */
export function AuthScreen({ flow, art }: AuthScreenProps) {
  const markRef = useRef<HTMLDivElement>(null);
  const { mode, replayKey } = useAuthIntro(markRef);
  const reveal = cn(introRevealClass(mode), "motion-reduce:animate-none");
  const copy = authCopy[flow];

  return (
    <div className="flex min-h-dvh w-full gap-3 p-3">
      <section className="relative isolate flex flex-1 flex-col px-6 py-6 sm:px-12 lg:max-w-[44rem]">
        {/* El fondo va en su propia capa: el logo vive adentro y tiene que verse antes que el recuadro. */}
        <div
          aria-hidden
          className={cn(
            "absolute inset-0 -z-10 rounded-[2rem] bg-white/70 shadow-[0_18px_50px_-30px_rgb(30_64_175/0.35)] ring-1 ring-white",
            introCardClass(mode),
            "motion-reduce:animate-none",
          )}
        />
        <Link
          href="/"
          className={cn(
            "inline-flex w-fit items-center gap-1.5 rounded-full px-3 py-1.5 text-sm font-medium text-slate-500 transition-colors hover:bg-slate-900/5 hover:text-slate-900",
            reveal,
          )}
        >
          <ArrowLeft className="size-4" aria-hidden />
          {authCopy.back}
        </Link>

        <div className="mx-auto flex w-full max-w-sm flex-1 flex-col justify-center py-10">
          {/* Arranca invisible y el hook lo anima desde el navbar o desde el centro. */}
          <div ref={markRef} className={cn("relative z-10 w-fit", mode === "pending" && "opacity-0")}>
            <Link href="/" aria-label="Inicio">
              <BrandLogo intro={mode === "direct"} replayKey={replayKey} />
            </Link>
          </div>

          <div className={reveal}>
            <h1 className="mt-10 text-3xl font-bold tracking-tight text-slate-900 sm:text-[2.5rem] sm:leading-tight">
              {copy.title}
            </h1>
            <p className="mt-3 text-base leading-relaxed text-slate-600">{copy.description}</p>

            <div className="mt-9">
              <Suspense fallback={<div className="h-[7.5rem]" />}>
                <OAuthButtons flow={flow} />
              </Suspense>
            </div>
          </div>
        </div>

        <p className={cn("flex items-start gap-2 text-xs leading-relaxed text-slate-500", reveal)}>
          <ShieldCheck className="size-4 shrink-0 text-emerald-500" aria-hidden />
          {authCopy.privacy}
        </p>
      </section>

      <aside aria-hidden className={cn("hidden min-h-full flex-1 lg:block", reveal)}>
        {art}
      </aside>
    </div>
  );
}
