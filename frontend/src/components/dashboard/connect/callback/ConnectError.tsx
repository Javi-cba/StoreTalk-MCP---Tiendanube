"use client";

import { SignOutButton } from "@clerk/nextjs";
import { Home, TriangleAlert, UserRoundCog } from "lucide-react";
import { Button, ButtonLink } from "@/components/ui/button";
import { GlassPanel } from "@/components/ui/glass";
import { connectCopy, getConnectError } from "@/content/connect";
import { ConnectStoreButton } from "../ConnectStoreButton";

type ConnectErrorProps = {
  code: string;
  /** Mensaje del backend (ya en español). */
  message: string;
};

/** Falla de la conexión: qué pasó y opciones para seguir; mismo panel de pantalla completa que la carga. */
export function ConnectError({ code, message }: ConnectErrorProps) {
  const copy = connectCopy.error;
  const error = getConnectError(code);
  const description = error.description ?? message;

  return (
    <GlassPanel
      role="alert"
      className="flex w-full flex-1 animate-rise-in flex-col items-center justify-center p-6 text-center motion-reduce:animate-none sm:p-8"
    >
      <span className="grid size-16 animate-pop-in place-items-center rounded-full bg-rose-500 text-white shadow-lg shadow-rose-500/30 ring-8 ring-rose-100 motion-reduce:animate-none">
        <TriangleAlert className="size-8" aria-hidden />
      </span>
      <p className="mt-5 text-xs font-semibold tracking-wider text-rose-600 uppercase">{copy.eyebrow}</p>
      <h1 className="mt-2 text-2xl font-bold tracking-tight text-balance text-slate-900 sm:text-3xl">{error.title}</h1>
      {description && <p className="mt-3 max-w-lg leading-relaxed text-slate-600">{description}</p>}
      <p className="mt-4 rounded-full bg-slate-900/5 px-3 py-1 font-mono text-xs text-slate-500">
        {copy.codeLabel}: {code}
      </p>

      <div className="mt-8 flex w-full max-w-sm flex-col gap-3">
        {error.actions.map((action) => {
          if (action === "reconnect") {
            return <ConnectStoreButton key={action} label={copy.actions.reconnect} />;
          }
          if (action === "switch-account") {
            return (
              <SignOutButton key={action} redirectUrl="/sign-in?redirect_url=/connect">
                <Button variant="glass">
                  <UserRoundCog className="size-4" aria-hidden />
                  {copy.actions["switch-account"]}
                </Button>
              </SignOutButton>
            );
          }
          return (
            <ButtonLink key={action} href="/" variant="ghost">
              <Home className="size-4" aria-hidden />
              {copy.actions.home}
            </ButtonLink>
          );
        })}
      </div>
    </GlassPanel>
  );
}
