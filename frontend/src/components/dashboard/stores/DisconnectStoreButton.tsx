"use client";

import { useAuth } from "@clerk/nextjs";
import { useState } from "react";
import { Unplug } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ConfirmDialog } from "@/components/ui/modal";
import { dashboardCopy } from "@/content/dashboard";
import { ApiError } from "@/lib/api/client";
import { disconnectStore } from "@/lib/api/stores";

type DisconnectStoreButtonProps = {
  connectionId: string;
  storeName: string;
  onDisconnected: (connectionId: string) => void;
};

/** "Desconectar tienda" con confirmación: solo llama al backend si el usuario acepta. */
export function DisconnectStoreButton({ connectionId, storeName, onDisconnected }: DisconnectStoreButtonProps) {
  const { getToken } = useAuth();
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const copy = dashboardCopy.disconnectDialog;

  const confirm = async () => {
    setLoading(true);
    setError(null);
    try {
      await disconnectStore(await getToken(), connectionId);
      setOpen(false);
      onDisconnected(connectionId);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Ocurrió un error inesperado.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <Button variant="danger-ghost" className="h-10 px-4" onClick={() => setOpen(true)}>
        <Unplug className="size-4" aria-hidden />
        {dashboardCopy.card.disconnect}
      </Button>
      <ConfirmDialog
        open={open}
        tone="danger"
        title={copy.title}
        description={
          <>
            <p>{copy.description(storeName)}</p>
            <p className="mt-2 text-slate-500">{copy.uninstallHint}</p>
          </>
        }
        confirmLabel={copy.confirm}
        cancelLabel={copy.cancel}
        loading={loading}
        error={error}
        onConfirm={confirm}
        onCancel={() => {
          setOpen(false);
          setError(null);
        }}
      />
    </>
  );
}
