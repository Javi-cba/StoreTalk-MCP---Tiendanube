"use client";

import { CircleCheck, ExternalLink, ShieldCheck } from "lucide-react";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { GlassPanel } from "@/components/ui/glass";
import { authorizeCopy } from "@/content/authorize";
import type { AuthorizationRequest } from "@/lib/schemas/oauth";
import { ConnectionVisual } from "./ConnectionVisual";
import { StorePicker } from "./StorePicker";

type ConsentPanelProps = {
  request: AuthorizationRequest;
  submitting: "approve" | "deny" | null;
  error: string | null;
  onApprove: (connectionId: string) => void;
  onDeny: () => void;
};

/** Quién pide acceso y qué va a poder hacer (izquierda); qué tienda compartir y la decisión (derecha). */
export function ConsentPanel({ request, submitting, error, onApprove, onDeny }: ConsentPanelProps) {
  const copy = authorizeCopy.consent;
  // Con una sola tienda ya queda elegida.
  const [selected, setSelected] = useState<string | null>(
    request.stores.length === 1 ? request.stores[0].connection_id : null,
  );

  return (
    <GlassPanel className="grid w-full max-w-4xl animate-rise-in grid-cols-1 gap-8 p-6 motion-reduce:animate-none sm:p-8 md:grid-cols-2 md:gap-10">
      <div className="flex flex-col">
        <ConnectionVisual clientName={request.client.name} mascot="idle" mascotAlt="" />
        <p className="mt-6 text-xs font-semibold tracking-wider text-brand uppercase">{copy.eyebrow}</p>
        <h1 className="mt-2 text-2xl font-bold tracking-tight text-balance text-slate-900 sm:text-3xl">
          {copy.title(request.client.name)}
        </h1>
        <p className="mt-3 leading-relaxed text-slate-600">{copy.description}</p>

        <h2 className="mt-6 text-sm font-semibold text-slate-900">{copy.canTitle}</h2>
        <ul className="mt-3 space-y-2.5">
          {copy.can.map((item) => (
            <li key={item} className="flex items-start gap-2.5 text-sm text-slate-700">
              <CircleCheck className="mt-0.5 size-4 shrink-0 text-emerald-500" aria-hidden />
              {item}
            </li>
          ))}
        </ul>
      </div>

      <div className="flex min-w-0 flex-col">
        <StorePicker
          stores={request.stores}
          selected={selected}
          onSelect={setSelected}
          disabled={submitting !== null}
        />

        <p className="mt-4 inline-flex items-center gap-1.5 text-sm text-slate-500">
          <ExternalLink className="size-3.5 shrink-0" aria-hidden />
          {copy.returnsTo} <span className="font-semibold text-slate-700">{request.client.redirect_host}</span>
        </p>

        {error && (
          <p role="alert" className="mt-4 rounded-xl bg-rose-50 px-3 py-2 text-sm text-rose-700 ring-1 ring-rose-100">
            {error}
          </p>
        )}

        <div className="mt-auto flex flex-col gap-3 pt-6">
          <Button
            loading={submitting === "approve"}
            disabled={!selected || submitting !== null}
            onClick={() => selected && onApprove(selected)}
          >
            {copy.approve}
          </Button>
          <Button variant="ghost" loading={submitting === "deny"} disabled={submitting !== null} onClick={onDeny}>
            {copy.deny}
          </Button>
          <p className="flex items-start gap-1.5 text-xs text-slate-500">
            <ShieldCheck className="mt-px size-3.5 shrink-0" aria-hidden />
            {copy.trustHint}
          </p>
        </div>
      </div>
    </GlassPanel>
  );
}
