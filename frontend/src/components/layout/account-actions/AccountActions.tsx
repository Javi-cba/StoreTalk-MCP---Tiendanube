"use client";

import { SignOutButton, UserButton } from "@clerk/nextjs";
import { LogOut, Store } from "lucide-react";
import { usePathname } from "next/navigation";
import { ButtonLink } from "@/components/ui/button";
import { navigation } from "@/content/site";
import { buttonStyles } from "@/components/ui/button/buttonStyles";

/** Derecha del navbar del área privada: cerrar sesión, "Mis tiendas" y la foto de perfil. Dentro de ClerkProvider. */
export function AccountActions() {
  const pathname = usePathname();

  return (
    <>
      <SignOutButton redirectUrl="/">
        <button type="button" className={buttonStyles("ghost", "h-10 px-4")}>
          <LogOut className="size-4" aria-hidden />
          <span className="hidden sm:inline">{navigation.signOut.label}</span>
        </button>
      </SignOutButton>
      {!pathname.startsWith(navigation.dashboard.href) && (
        <ButtonLink href={navigation.dashboard.href} className="h-10 whitespace-nowrap px-5">
          <Store className="size-4" aria-hidden />
          {navigation.dashboard.label}
        </ButtonLink>
      )}
      {/* Foto de perfil del usuario logueado (abre el menú de cuenta de Clerk). */}
      <UserButton appearance={{ elements: { avatarBox: "size-10 ring-2 ring-white shadow-sm" } }} />
    </>
  );
}
