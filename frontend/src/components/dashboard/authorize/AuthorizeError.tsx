import { BookOpen, Store, TriangleAlert } from "lucide-react";
import { ButtonLink } from "@/components/ui/button";
import { GlassPanel } from "@/components/ui/glass";
import { authorizeCopy } from "@/content/authorize";

/** Pedido vencido, ya usado o sin request_id: hay que volver a empezar desde el asistente. */
export function AuthorizeError({ message }: { message: string }) {
  const copy = authorizeCopy.error;

  return (
    <GlassPanel
      role="alert"
      className="flex w-full flex-1 animate-rise-in flex-col items-center justify-center p-6 text-center motion-reduce:animate-none sm:p-8"
    >
      <span className="grid size-16 animate-pop-in place-items-center rounded-full bg-rose-500 text-white shadow-lg shadow-rose-500/30 ring-8 ring-rose-100 motion-reduce:animate-none">
        <TriangleAlert className="size-8" aria-hidden />
      </span>
      <p className="mt-5 text-xs font-semibold tracking-wider text-rose-600 uppercase">{copy.eyebrow}</p>
      <h1 className="mt-2 text-2xl font-bold tracking-tight text-balance text-slate-900 sm:text-3xl">{copy.title}</h1>
      <p className="mt-3 max-w-lg leading-relaxed text-slate-600">{message || copy.missing}</p>
      <div className="mt-8 flex w-full max-w-sm flex-col gap-3">
        <ButtonLink href="/connect-ai">
          <BookOpen className="size-4" aria-hidden />
          {copy.guide}
        </ButtonLink>
        <ButtonLink href="/dashboard" variant="ghost">
          <Store className="size-4" aria-hidden />
          {copy.home}
        </ButtonLink>
      </div>
    </GlassPanel>
  );
}
