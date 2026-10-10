"use client";

import { CircleCheck, Info, MessageCircle, ShieldCheck } from "lucide-react";
import { useState } from "react";
import { CopyField } from "@/components/ui/copy-field";
import { GlassPanel } from "@/components/ui/glass";
import { assistantGuideCopy, type AssistantClientId } from "@/content/assistantGuide";
import { MCP_URL } from "@/lib/mcp/url";
import { ClientTabs } from "./ClientTabs";
import { GuideSteps } from "./GuideSteps";

/** "Conectá tu IA": la URL del conector a la izquierda y el paso a paso por asistente a la derecha. */
export function AssistantGuide() {
  const copy = assistantGuideCopy;
  const [active, setActive] = useState<AssistantClientId>("claude");
  const client = copy.clients.find((c) => c.id === active) ?? copy.clients[0];

  return (
    <div className="mx-auto screen-fill w-full max-w-6xl px-4 pt-4 pb-10 sm:px-6">
      <header className="max-w-3xl">
        <p className="text-xs font-semibold tracking-wider text-brand uppercase">{copy.eyebrow}</p>
        <h1 className="mt-1 text-2xl font-bold tracking-tight text-balance text-slate-900 sm:text-3xl">{copy.title}</h1>
        <p className="mt-1 text-slate-600">{copy.description}</p>
      </header>

      <div className="mt-5 grid animate-rise-in gap-5 motion-reduce:animate-none grid-cols-1 lg:grid-cols-[minmax(0,2fr)_minmax(0,3fr)]">
        <div className="flex min-w-0 flex-col gap-5">
          <GlassPanel className="p-5 sm:p-6">
            <h2 className="text-sm font-semibold text-slate-900">{copy.urlLabel}</h2>
            <p className="mt-1 mb-3 text-sm text-slate-500">{copy.urlHint}</p>
            <CopyField value={MCP_URL} copyLabel={copy.copy} copiedLabel={copy.copied} />
          </GlassPanel>

          <GlassPanel className="flex flex-1 flex-col p-5 sm:p-6">
            <h2 className="text-sm font-semibold text-slate-900">{copy.benefitsTitle}</h2>
            <ul className="mt-3 space-y-2.5">
              {copy.benefits.map((benefit) => (
                <li key={benefit} className="flex items-start gap-2.5 text-sm text-slate-700">
                  <CircleCheck className="mt-0.5 size-4 shrink-0 text-emerald-500" aria-hidden />
                  {benefit}
                </li>
              ))}
            </ul>
            <p className="mt-4 flex items-start gap-2 rounded-xl bg-emerald-50/80 px-3 py-2.5 text-sm text-emerald-800 ring-1 ring-emerald-100">
              <ShieldCheck className="mt-0.5 size-4 shrink-0" aria-hidden />
              {copy.security}
            </p>
            <h2 className="mt-5 text-sm font-semibold text-slate-900">{copy.examplesTitle}</h2>
            <ul className="mt-3 flex flex-wrap gap-2">
              {copy.examples.map((example) => (
                <li
                  key={example}
                  className="flex items-start gap-2 rounded-2xl rounded-bl-md bg-white/80 px-3 py-1.5 text-sm text-slate-700 ring-1 ring-slate-200"
                >
                  <MessageCircle className="mt-0.5 size-4 shrink-0 text-brand" aria-hidden />
                  {example}
                </li>
              ))}
            </ul>
          </GlassPanel>
        </div>

        <GlassPanel className="flex min-w-0 flex-col p-5 sm:p-6">
          <ClientTabs clients={copy.clients} active={active} onChange={setActive} label={copy.clientsLabel} />

          <div
            key={client.id}
            role="tabpanel"
            id={`panel-${client.id}`}
            aria-labelledby={`tab-${client.id}`}
            className="mt-5 flex flex-1 flex-col"
          >
            <p className="mb-4 inline-flex items-center gap-2 self-start rounded-full bg-blue-50 px-3 py-1 text-xs font-medium text-blue-800 ring-1 ring-blue-100">
              {client.availability}
            </p>
            <GuideSteps steps={client.steps} mcpUrl={MCP_URL} />
            <p className="mt-auto flex items-start gap-1.5 pt-4 text-xs text-slate-500">
              <Info className="mt-px size-3.5 shrink-0" aria-hidden />
              {copy.menuNote}
            </p>
          </div>
        </GlassPanel>
      </div>
    </div>
  );
}
