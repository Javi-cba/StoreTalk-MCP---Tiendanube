"use client";

import Link from "next/link";
import { ArrowRight, Store } from "lucide-react";
import { ButtonLink } from "@/components/ui/button";
import { navigation } from "@/content/site";
import { useHasSession } from "@/hooks/useHasSession";
import { cn } from "@/lib/utils/cn";

const navLinkClass =
  "inline-flex h-10 items-center rounded-full px-4 text-sm font-medium text-slate-600 transition-colors hover:bg-white/70 hover:text-slate-900 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand";

/** Derecha del navbar de la landing: "Ingresar" + "Conectar mi tienda" sin sesión, "Mis tiendas" con sesión. */
export function NavbarActions() {
  const signedIn = useHasSession();

  if (signedIn) {
    return (
      <ButtonLink href={navigation.dashboard.href} className="h-10 whitespace-nowrap px-5">
        <Store className="size-4" aria-hidden />
        {navigation.dashboard.label}
      </ButtonLink>
    );
  }

  return (
    <>
      <Link href={navigation.signIn.href} className={cn(navLinkClass, "hidden lg:inline-flex")}>
        {navigation.signIn.label}
      </Link>
      <ButtonLink href={navigation.cta.href} className="h-10 whitespace-nowrap px-5">
        {navigation.cta.label}
        <ArrowRight className="size-4" />
      </ButtonLink>
    </>
  );
}
