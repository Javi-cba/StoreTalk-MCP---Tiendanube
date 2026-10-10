import { scopeAccess, scopeResources } from "@/content/connect";

export type ScopeInfo = {
  scope: string;
  access: "read" | "write" | null;
  /** Ej. "Productos". */
  resource: string;
  /** Ej. "Crear y editar". */
  accessLabel: string | null;
};

function humanize(value: string): string {
  const text = value.replaceAll("_", " ");
  return text.charAt(0).toUpperCase() + text.slice(1);
}

/** "write_products" → { access: "write", resource: "Productos", accessLabel: "Crear y editar" }. */
export function describeScope(scope: string): ScopeInfo {
  const match = /^(read|write)_(.+)$/.exec(scope);
  if (!match) {
    return { scope, access: null, resource: humanize(scope), accessLabel: null };
  }
  const access = match[1] as "read" | "write";
  const key = match[2];
  return {
    scope,
    access,
    resource: scopeResources[key] ?? humanize(key),
    accessLabel: scopeAccess[access],
  };
}

export type ScopeGroup = {
  /** Clave del recurso en Tiendanube, ej. "products". */
  key: string;
  /** Ej. "Productos". */
  resource: string;
  /** Solo los scopes que vienen en el token, en orden: lectura primero. Nada se infiere. */
  grants: ScopeInfo[];
};

const ACCESS_ORDER = { read: 0, write: 1 } as const;

/** Un grupo por recurso con los permisos reales del token (read_products + write_products → "Productos"). */
export function groupScopes(scopes: readonly string[]): ScopeGroup[] {
  const groups = new Map<string, ScopeGroup>();
  for (const info of new Set(scopes)) {
    const scope = describeScope(info);
    const key = scope.access ? scope.scope.slice(scope.access.length + 1) : scope.scope;
    const group = groups.get(key) ?? { key, resource: scope.resource, grants: [] };
    group.grants.push(scope);
    groups.set(key, group);
  }
  const hasWrite = (g: ScopeGroup) => g.grants.some((s) => s.access === "write");
  return [...groups.values()]
    .map((g) => ({
      ...g,
      grants: g.grants.toSorted(
        (a, b) => (a.access ? ACCESS_ORDER[a.access] : 2) - (b.access ? ACCESS_ORDER[b.access] : 2),
      ),
    }))
    .sort((a, b) => Number(hasWrite(b)) - Number(hasWrite(a)) || a.resource.localeCompare(b.resource, "es"));
}
