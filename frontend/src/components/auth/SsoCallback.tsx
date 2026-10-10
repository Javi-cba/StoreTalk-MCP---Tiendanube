"use client";

import { HandleSSOCallback, useClerk, useSignIn } from "@clerk/nextjs";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { LoadingMascot } from "@/components/ui/loading-mascot";
import { authCopy } from "@/content/auth";
import { consumeAfterAuth, peekAfterAuth } from "@/lib/auth/redirect";

/** Vuelta de Google/Apple: Clerk termina de crear la sesión y seguimos al destino guardado. */
export function SsoCallback() {
  const router = useRouter();
  const clerk = useClerk();
  const { signIn } = useSignIn();
  const [checked, setChecked] = useState(false);
  const copy = authCopy.callback;

  useEffect(() => {
    if (!clerk.loaded || checked) return;
    const intent = new URLSearchParams(window.location.search).get("intent");
    // Clerk convierte solo un login sin cuenta en un registro (isTransferable). Desde "Iniciar
    // sesión" no queremos crear cuentas: se manda a la pantalla de registro.
    if (intent === "signIn" && signIn.status !== "complete" && signIn.isTransferable) {
      const destination = peekAfterAuth();
      const redirect = destination ? `&redirect_url=${encodeURIComponent(destination)}` : "";
      router.replace(`/sign-up?notice=no-account${redirect}`);
      return;
    }
    // eslint-disable-next-line react-hooks/set-state-in-effect -- depende del estado de Clerk ya cargado
    setChecked(true);
  }, [clerk.loaded, checked, signIn, router]);

  return (
    <div role="status" aria-live="polite" className="mx-auto flex w-full max-w-md flex-col items-center px-4 pb-16 text-center sm:px-6">
      <LoadingMascot alt={copy.imageAlt} />
      <h1 className="mt-2 text-2xl font-bold tracking-tight text-balance text-slate-900 sm:text-3xl">{copy.title}</h1>
      <p className="mt-3 text-base leading-relaxed text-slate-600">{copy.description}</p>

      {/* Recién después del chequeo: HandleSSOCallback haría la transferencia a registro. */}
      {checked && (
        <HandleSSOCallback
          navigateToApp={({ decorateUrl }) => {
            const destination = decorateUrl(consumeAfterAuth());
            if (destination.startsWith("http")) {
              window.location.href = destination;
              return;
            }
            router.replace(destination);
          }}
          // Pasos extra (verificaciones) que esta UI no maneja: se vuelve con un aviso.
          navigateToSignIn={() => router.replace("/sign-in?error=verification")}
          navigateToSignUp={() => router.replace("/sign-up?error=verification")}
        />
      )}
    </div>
  );
}
