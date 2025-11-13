export type PaginationItem =
  | { type: "page"; value: number }
  | { type: "ellipsis" };

/**
 * Build a Google-like pagination model with first/last pages and ellipses.
 */
export function buildPaginationItems(
  currentPage: number,
  totalPages: number
): PaginationItem[] {
  const items: PaginationItem[] = [];
  if (totalPages <= 0) {
    return items;
  }

  const addPage = (page: number) => {
    if (page < 1 || page > totalPages) return;
    if (!items.some((item) => item.type === "page" && item.value === page)) {
      items.push({ type: "page", value: page });
    }
  };

  const addEllipsis = () => {
    const lastItem = items.at(-1);
    if (!lastItem || lastItem.type !== "ellipsis") {
      items.push({ type: "ellipsis" });
    }
  };

  if (totalPages <= 5) {
    for (let page = 1; page <= totalPages; page += 1) {
      addPage(page);
    }
    return items;
  }

  addPage(1);

  let start = Math.max(2, currentPage - 1);
  let end = Math.min(totalPages - 1, currentPage + 1);

  if (currentPage <= 3) {
    start = 2;
    end = 4;
  } else if (currentPage >= totalPages - 2) {
    start = totalPages - 3;
    end = totalPages - 1;
  }

  if (start > 2) {
    addEllipsis();
  }

  for (let page = start; page <= end; page += 1) {
    addPage(page);
  }

  if (end < totalPages - 1) {
    addEllipsis();
  }

  addPage(totalPages);
  return items;
}
