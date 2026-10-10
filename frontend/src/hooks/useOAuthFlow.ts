"use client";

import { useAuth, useSignIn, useSignUp } from "@clerk/nextjs";
import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";
import { authCopy, type AuthFlow, type OAuthProvider } from "@/content/auth";
import { rememberAfterAuth, safeRedirectPath } from "@/lib/auth/redirect";

export const SSO_CALLBACK_PATH = "/sso-callback";

/** Clerk no deja abrir otra sesión encima de una activa ("You're already signed in"). */
function isSessionExists(error: { code?: string; errors?: { code?: string }[] }): boolean {
  return error.code === "session_exists" || Boolean(error.errors?.some((e) => e.code === "session_exists"));
}

/** Login/registro con Google o Apple usando el flujo custom de Clerk (sin sus componentes). */
export function useOAuthFlow(flow: AuthFlow) {
  const { signIn } = useSignIn();
  const { signUp } = useSignUp();
  const { isLoaded, isSignedIn } = useAuth();
  const router = useRouter();
  const searchParams = useSearchParams();
  const [pending, setPending] = useState<OAuthProvider | null>(null);
  const [error, setError] = useState<string | null>(() =>
    searchParams.get("error") === "verification" ? authCopy.errors.verification : null,
  );
  // Viene de un "Iniciar sesión" con un email sin cuenta (ver SsoCallback).
  const notice = searchParams.get("notice") === "no-account" ? authCopy.notices.noAccount : null;

  const redirectParam = searchParams.get("redirect_url");

  // Con la sesión ya iniciada no tiene sentido el login: se sigue directo al destino.
  useEffect(() => {
    if (isLoaded && isSignedIn) router.replace(safeRedirectPath(redirectParam));
  }, [isLoaded, isSignedIn, redirectParam, router]);

  async function start(strategy: OAuthProvider) {
    setPending(strategy);
    setError(null);
    const destination = safeRedirectPath(redirectParam);
    rememberAfterAuth(destination);

    const params = {
      strategy,
      redirectUrl: new URL(destination, window.location.origin).href,
      // `intent` lo leen SsoCallback y HandleSSOCallback para saber desde qué pantalla se arrancó.
      redirectCallbackUrl: new URL(`${SSO_CALLBACK_PATH}?intent=${flow}`, window.location.origin).href,
    };
    // Si sale bien, Clerk redirige al proveedor y esta pantalla se va.
    const { error: ssoError } = flow === "signIn" ? await signIn.sso(params) : await signUp.sso(params);
    if (ssoError) {
      if (isSessionExists(ssoError)) {
        router.replace(destination);
        return;
      }
      setError(authCopy.errors.generic);
      setPending(null);
    }
  }

  return { start, pending, error, notice, redirectParam };
}
