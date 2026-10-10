export type PageItem = { type: "page"; page: number } | { type: "gap"; key: string };

/**
 * Números a mostrar en un paginador: siempre la primera, la última y las vecinas de la actual;
 * el resto se resume con "…". Ej. página 6 de 12 → 1 … 5 6 7 … 12.
 */
export function getPageItems(current: number, total: number, siblings = 1): PageItem[] {
  const pages = new Set([1, total]);
  for (let page = current - siblings; page <= current + siblings; page++) {
    if (page >= 1 && page <= total) pages.add(page);
  }
  const sorted = [...pages].sort((a, b) => a - b);

  const items: PageItem[] = [];
  sorted.forEach((page, index) => {
    const previous = sorted[index - 1];
    if (previous !== undefined && page - previous === 2) items.push({ type: "page", page: previous + 1 });
    else if (previous !== undefined && page - previous > 2) items.push({ type: "gap", key: `gap-${previous}` });
    items.push({ type: "page", page });
  });
  return items;
}
