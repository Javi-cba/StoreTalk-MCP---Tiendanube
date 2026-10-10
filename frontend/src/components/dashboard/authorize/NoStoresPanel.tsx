import { TiendanubeIcon } from "@/components/ui/icons";
import { Button } from "@/components/ui/button";
import { GlassPanel } from "@/components/ui/glass";
import { authorizeCopy } from "@/content/authorize";
import { ConnectStoreButton } from "../connect/ConnectStoreButton";

type NoStoresPanelProps = {
  submitting: boolean;
  onDeny: () => void;
};

/** El usuario todavía no conectó ninguna tienda: no hay nada que compartir con el asistente. */
export function NoStoresPanel({ submitting, onDeny }: NoStoresPanelProps) {
  const copy = authorizeCopy.noStores;

  return (
    <GlassPanel className="flex w-full max-w-md animate-rise-in flex-col items-center p-8 text-center motion-reduce:animate-none">
      <span className="grid size-14 place-items-center rounded-2xl bg-linear-to-br from-blue-600 to-sky-400 text-white shadow-lg shadow-blue-600/30">
        <TiendanubeIcon size={30} />
      </span>
      <h1 className="mt-5 text-xl font-bold tracking-tight text-slate-900">{copy.title}</h1>
      <p className="mt-2 leading-relaxed text-slate-600">{copy.description}</p>
      <div className="mt-8 flex w-full flex-col gap-3">
        <ConnectStoreButton label={copy.cta} />
        <Button variant="ghost" loading={submitting} onClick={onDeny}>
          {copy.deny}
        </Button>
      </div>
    </GlassPanel>
  );
}
