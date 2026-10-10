"use client";

import { ArrowRight, Store } from "lucide-react";
import { ButtonLink } from "@/components/ui/button";
import { hero } from "@/content/home";
import { useHasSession } from "@/hooks/useHasSession";

/** CTA principal del hero: con sesión iniciada lleva a "Mis tiendas" en vez de conectar. */
export function HeroPrimaryCta() {
  const signedIn = useHasSession();
  const cta = signedIn ? hero.dashboardCta : hero.primaryCta;

  return (
    <ButtonLink href={cta.href}>
      {signedIn && <Store className="size-4" aria-hidden />}
      {cta.label}
      {!signedIn && <ArrowRight className="size-4" />}
    </ButtonLink>
  );
}
