import { groupScopes } from "@/lib/utils/scopes";
import { ScopeCard } from "./ScopeCard";

type ScopeListProps = {
  scopes: readonly string[];
  emptyLabel: string;
};

/** Permisos que el comerciante aceptó en Tiendanube, agrupados en una card por entidad. */
export function ScopeList({ scopes, emptyLabel }: ScopeListProps) {
  if (scopes.length === 0) {
    return <p className="text-sm text-slate-500">{emptyLabel}</p>;
  }

  return (
    <ul className="grid gap-2 sm:grid-cols-2">
      {groupScopes(scopes).map((group) => (
        <ScopeCard key={group.key} group={group} />
      ))}
    </ul>
  );
}
