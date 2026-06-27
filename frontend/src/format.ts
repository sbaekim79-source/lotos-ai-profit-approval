export function formatJPY(value: number | null | undefined) {
  const formatted = new Intl.NumberFormat("en-US", {
    maximumFractionDigits: 0,
  }).format(value ?? 0);
  return `JPY ${formatted}`;
}

export function formatRate(value: number | null | undefined) {
  return `${((value ?? 0) * 100).toFixed(1)}%`;
}
