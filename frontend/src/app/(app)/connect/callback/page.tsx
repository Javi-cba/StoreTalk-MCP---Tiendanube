import type { Metadata } from "next";
import { Suspense } from "react";
import { CallbackLoading, ConnectCallback } from "@/components/dashboard/connect/callback";
import { connectCopy } from "@/content/connect";
import { site } from "@/content/site";

export const metadata: Metadata = { title: `${connectCopy.callback.metaTitle} · ${site.name}` };

/** Vuelta del OAuth de Tiendanube (?code=...&state=...). Los estados llenan el alto visible, al ancho de la navbar. */
export default function ConnectCallbackPage() {
  return (
    <div className="flex screen-fill flex-col px-4 py-6 sm:px-6">
      <div className="mx-auto flex w-full max-w-6xl flex-1 flex-col items-center justify-center">
        {/* useSearchParams necesita un Suspense para que el resto de la página se prerenderice. */}
        <Suspense fallback={<CallbackLoading />}>
          <ConnectCallback />
        </Suspense>
      </div>
    </div>
  );
}
