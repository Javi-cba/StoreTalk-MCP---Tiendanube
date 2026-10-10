"use client";

import Link from "next/link";
import { CircleAlert, Info, LoaderCircle } from "lucide-react";
import { AppleIcon, GoogleIcon } from "@/components/ui/icons";
import { authCopy, type AuthFlow, type OAuthProvider } from "@/content/auth";
import { useOAuthFlow } from "@/hooks/useOAuthFlow";
import { cn } from "@/lib/utils/cn";

const providers: { strategy: OAuthProvider; icon: typeof GoogleIcon; className: string }[] = [
  {
    strategy: "oauth_google",
    icon: GoogleIcon,
    className: "bg-white text-slate-800 ring-1 ring-slate-200 hover:bg-slate-50 hover:ring-slate-300",
  },
  {
    strategy: "oauth_apple",
    icon: AppleIcon,
    className: "bg-slate-950 text-white shadow-lg shadow-slate-900/20 hover:bg-slate-800",
  },
];

export function OAuthButtons({ flow }: { flow: AuthFlow }) {
  const { start, pending, error, notice, redirectParam } = useOAuthFlow(flow);
  const switchLink = authCopy[flow].switchLink;
  // Mantiene el destino (ej. /connect/callback?code=...) al pasar entre login y registro.
  const switchHref = redirectParam
    ? `${switchLink.href}?redirect_url=${encodeURIComponent(redirectParam)}`
    : switchLink.href;

  return (
    <>
      {notice && !error && (
        <p role="status" className="mb-4 flex items-start gap-2 rounded-2xl bg-blue-50 px-4 py-3 text-sm text-blue-800 ring-1 ring-blue-100">
          <Info className="mt-0.5 size-4 shrink-0" aria-hidden />
          {notice}
        </p>
      )}

      <div className="space-y-3">
        {providers.map(({ strategy, icon: Icon, className }) => (
          <button
            key={strategy}
            type="button"
            onClick={() => start(strategy)}
            disabled={pending !== null}
            aria-busy={pending === strategy || undefined}
            className={cn(
              "flex h-13 w-full cursor-pointer items-center justify-center gap-3 rounded-2xl text-[0.95rem] font-semibold transition-all focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand active:scale-[0.99] disabled:cursor-default disabled:opacity-60",
              className,
            )}
          >
            {pending === strategy ? <LoaderCircle className="size-5 animate-spin" aria-hidden /> : <Icon size={20} />}
            {authCopy.providers[strategy]}
          </button>
        ))}
      </div>

      {error && (
        <p role="alert" className="mt-4 flex items-start gap-2 rounded-2xl bg-rose-50 px-4 py-3 text-sm text-rose-700 ring-1 ring-rose-100">
          <CircleAlert className="mt-0.5 size-4 shrink-0" aria-hidden />
          {error}
        </p>
      )}

      {/* Clerk monta acá el captcha invisible de bot protection cuando lo necesita. */}
      <div id="clerk-captcha" className="mt-3" />

      <p className="mt-6 text-sm text-slate-600">
        {authCopy[flow].switchPrompt}{" "}
        <Link href={switchHref} className="font-semibold text-brand underline-offset-4 hover:underline">
          {switchLink.label}
        </Link>
      </p>
    </>
  );
}
