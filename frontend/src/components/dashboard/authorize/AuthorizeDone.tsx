import Image from "next/image";
import { Check, Undo2 } from "lucide-react";
import { GlassPanel } from "@/components/ui/glass";
import { authorizeCopy } from "@/content/authorize";

type AuthorizeDoneProps = {
  outcome: "approved" | "denied";
  clientName: string;
  url: string;
};

/** Resultado antes de volver al asistente: festejo si se aprobó, aviso neutro si se canceló. */
export function AuthorizeDone({ outcome, clientName, url }: AuthorizeDoneProps) {
  const copy = authorizeCopy.done;
  const approved = outcome === "approved";
  const text = approved ? copy.approved : copy.denied;

  return (
    <GlassPanel
      role="status"
      aria-live="polite"
      className="flex w-full max-w-md animate-rise-in flex-col items-center p-8 text-center motion-reduce:animate-none"
    >
      {approved ? (
        <div className="relative">
          <div aria-hidden className="absolute inset-6 rounded-full bg-linear-to-tr from-emerald-300/40 to-sky-300/40 blur-2xl" />
          {/* 480x534; unoptimized para que Next no pierda la animación del webp. */}
          <Image
            src="/brand/mascot-celebrate.webp"
            alt={copy.approved.mascotAlt}
            width={480}
            height={534}
            priority
            unoptimized
            className="relative h-auto w-32"
          />
          <span className="absolute right-0 bottom-2 grid size-9 animate-pop-in place-items-center rounded-full bg-emerald-500 text-white shadow-lg shadow-emerald-500/30 ring-4 ring-white motion-reduce:animate-none">
            <Check className="size-4.5" strokeWidth={3} aria-hidden />
          </span>
        </div>
      ) : (
        <span className="grid size-16 animate-pop-in place-items-center rounded-full bg-slate-700 text-white shadow-lg ring-8 ring-slate-100 motion-reduce:animate-none">
          <Undo2 className="size-7" aria-hidden />
        </span>
      )}

      <p className={approved ? "mt-4 text-xs font-semibold tracking-wider text-emerald-600 uppercase" : "mt-5 text-xs font-semibold tracking-wider text-slate-500 uppercase"}>
        {text.eyebrow}
      </p>
      <h1 className="mt-2 text-xl font-bold tracking-tight text-balance text-slate-900 sm:text-2xl">
        {approved ? copy.approved.title(clientName) : copy.denied.title}
      </h1>
      <p className="mt-2 inline-flex items-center gap-2 text-sm text-slate-600">
        <span aria-hidden className="flex gap-1">
          {[0, 150, 300].map((delay) => (
            <span
              key={delay}
              style={{ animationDelay: `${delay}ms` }}
              className="size-1.5 animate-bounce rounded-full bg-brand motion-reduce:animate-none"
            />
          ))}
        </span>
        {text.description}
      </p>
      <a href={url} className="mt-5 text-sm font-medium text-brand underline-offset-4 hover:underline">
        {copy.manual}
      </a>
    </GlassPanel>
  );
}
