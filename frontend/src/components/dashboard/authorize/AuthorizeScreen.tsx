"use client";

import { useSearchParams } from "next/navigation";
import { useAuthorizationRequest } from "@/hooks/useAuthorizationRequest";
import { AuthorizeDone } from "./AuthorizeDone";
import { AuthorizeError } from "./AuthorizeError";
import { AuthorizeLoading } from "./AuthorizeLoading";
import { ConsentPanel } from "./ConsentPanel";
import { NoStoresPanel } from "./NoStoresPanel";

/** /authorize?request_id=...: el asistente de IA pide acceso y el usuario elige qué tienda compartir. */
export function AuthorizeScreen() {
  const { state, decide } = useAuthorizationRequest(useSearchParams().get("request_id"));

  if (state.status === "loading") return <AuthorizeLoading />;
  if (state.status === "error") return <AuthorizeError message={state.message} />;
  if (state.status === "redirecting") {
    return <AuthorizeDone outcome={state.outcome} clientName={state.request.client.name} url={state.url} />;
  }
  if (state.request.stores.length === 0) {
    return <NoStoresPanel submitting={state.submitting === "deny"} onDeny={() => decide("deny")} />;
  }
  return (
    <ConsentPanel
      request={state.request}
      submitting={state.submitting}
      error={state.error}
      onApprove={(connectionId) => decide("approve", connectionId)}
      onDeny={() => decide("deny")}
    />
  );
}
