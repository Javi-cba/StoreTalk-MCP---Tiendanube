"use client";

import { useEffect, useRef, type ReactNode } from "react";
import { TriangleAlert } from "lucide-react";
import { Button } from "@/components/ui/button";

type ConfirmDialogProps = {
  open: boolean;
  title: string;
  description: ReactNode;
  confirmLabel: string;
  cancelLabel: string;
  /** "danger" para acciones destructivas (botón rojo + ícono de alerta). */
  tone?: "default" | "danger";
  /** Mientras confirma: spinner y no se puede cerrar. */
  loading?: boolean;
  /** Error de la última confirmación, se muestra dentro del modal. */
  error?: string | null;
  onConfirm: () => void;
  onCancel: () => void;
};

/** Modal de confirmación con <dialog> nativo: foco atrapado, Esc y fondo bloqueado sin librerías. */
export function ConfirmDialog({
  open,
  title,
  description,
  confirmLabel,
  cancelLabel,
  tone = "default",
  loading = false,
  error,
  onConfirm,
  onCancel,
}: ConfirmDialogProps) {
  const ref = useRef<HTMLDialogElement>(null);

  useEffect(() => {
    const dialog = ref.current;
    if (!dialog) return;
    if (open && !dialog.open) dialog.showModal();
    if (!open && dialog.open) dialog.close();
  }, [open]);

  const cancel = () => {
    if (!loading) onCancel();
  };

  return (
    <dialog
      ref={ref}
      aria-labelledby="confirm-dialog-title"
      onCancel={(event) => {
        event.preventDefault(); // Esc: lo cerramos nosotros para respetar `loading`.
        cancel();
      }}
      onClick={(event) => {
        if (event.target === event.currentTarget) cancel(); // click en el fondo
      }}
      className="m-auto w-[calc(100%-2rem)] max-w-md rounded-3xl bg-white p-0 shadow-2xl ring-1 ring-slate-200 backdrop:bg-slate-900/40 backdrop:backdrop-blur-sm open:animate-rise-in motion-reduce:open:animate-none"
    >
      <div className="flex flex-col gap-4 p-6 sm:p-7">
        {tone === "danger" && (
          <span className="grid size-11 place-items-center rounded-2xl bg-rose-50 text-rose-600 ring-1 ring-rose-100">
            <TriangleAlert className="size-5" aria-hidden />
          </span>
        )}
        <div>
          <h2 id="confirm-dialog-title" className="text-lg font-semibold text-slate-900">
            {title}
          </h2>
          <div className="mt-2 text-sm leading-relaxed text-slate-600">{description}</div>
        </div>
        {error && (
          <p role="alert" className="rounded-xl bg-rose-50 px-3 py-2 text-sm text-rose-700">
            {error}
          </p>
        )}
        <div className="mt-2 flex flex-col-reverse gap-3 sm:flex-row sm:justify-end">
          <Button variant="glass" onClick={cancel} disabled={loading} className="h-11 ring-1 ring-slate-200">
            {cancelLabel}
          </Button>
          <Button
            variant={tone === "danger" ? "danger" : "primary"}
            onClick={onConfirm}
            loading={loading}
            className="h-11"
            autoFocus={tone !== "danger"}
          >
            {confirmLabel}
          </Button>
        </div>
      </div>
    </dialog>
  );
}
