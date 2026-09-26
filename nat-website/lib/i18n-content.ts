// Resolves an admin-entered translatable JSON field ({ az, en?, ru? }) to the visitor's
// locale, falling back to Azerbaijani when the requested locale's value is missing (FR-025).
export function localizeText(value: unknown, locale: string): string {
  if (value && typeof value === "object") {
    const record = value as Record<string, unknown>;
    const direct = record[locale];
    if (typeof direct === "string" && direct.length > 0) return direct;
    const fallback = record.az;
    if (typeof fallback === "string") return fallback;
  }
  return "";
}

export function localizeList(value: unknown, locale: string): string[] {
  if (value && typeof value === "object") {
    const record = value as Record<string, unknown>;
    const direct = record[locale];
    if (Array.isArray(direct) && direct.length > 0) return direct as string[];
    const fallback = record.az;
    if (Array.isArray(fallback)) return fallback as string[];
  }
  return [];
}
