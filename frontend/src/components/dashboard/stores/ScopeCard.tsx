import { Eye, KeyRound, PencilLine } from "lucide-react";
import type { ScopeGroup, ScopeInfo } from "@/lib/utils/scopes";
import { cn } from "@/lib/utils/cn";

/** Una entidad (Productos, Órdenes...) con los permisos que trae el token: nada inferido ni fijo. */
export function ScopeCard({ group }: { group: ScopeGroup }) {
  return (
    <li className="flex h-full flex-col gap-2 rounded-xl bg-white/80 px-3 py-2.5 ring-1 ring-slate-200">
      <span className="text-sm font-semibold text-slate-900">{group.resource}</span>
      <div className="flex flex-wrap gap-1.5">
        {group.grants.map((grant) => (
          <GrantChip key={grant.scope} grant={grant} />
        ))}
      </div>
    </li>
  );
}

function GrantChip({ grant }: { grant: ScopeInfo }) {
  const Icon = grant.access === "write" ? PencilLine : grant.access === "read" ? Eye : KeyRound;
  return (
    <span
      title={grant.scope}
      className={cn(
        "inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium whitespace-nowrap ring-1",
        grant.access === "write" ? "bg-blue-50 text-blue-800 ring-blue-200" : "bg-slate-50 text-slate-700 ring-slate-200",
      )}
    >
      <Icon className="size-3.5" aria-hidden />
      {grant.accessLabel ?? grant.scope}
    </span>
  );
}
