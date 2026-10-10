"use client";

import { useConnectCallback } from "@/hooks/useConnectCallback";
import { CallbackLoading } from "./CallbackLoading";
import { ConnectError } from "./ConnectError";
import { ConnectSuccess } from "./ConnectSuccess";

export function ConnectCallback() {
  const state = useConnectCallback();

  if (state.status === "success") return <ConnectSuccess store={state.store} />;
  if (state.status === "error") return <ConnectError code={state.code} message={state.message} />;
  return <CallbackLoading />;
}
