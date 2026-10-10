import type { Metadata } from "next";
import { Suspense } from "react";
import { AuthorizeLoading, AuthorizeScreen } from "@/components/dashboard/authorize";
import { authorizeCopy } from "@/content/authorize";
import { site } from "@/content/site";

export const metadata: Metadata = { title: `${authorizeCopy.metaTitle} · ${site.name}` };

/** Consentimiento del OAuth del MCP: llega desde el asistente de IA vía {PUBLIC_BASE_URL}/authorize. */
export default function AuthorizePage() {
  return (
    <div className="flex screen-fill flex-col px-4 py-6 sm:px-6">
      <div className="mx-auto flex w-full max-w-6xl flex-1 flex-col items-center justify-center">
        {/* useSearchParams necesita un Suspense para que el resto de la página se prerenderice. */}
        <Suspense fallback={<AuthorizeLoading />}>
          <AuthorizeScreen />
        </Suspense>
      </div>
    </div>
  );
}
