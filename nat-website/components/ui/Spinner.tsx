// Used when the pending content has no predictable shape (e.g. initial page load), unlike
// Skeleton which is for a known layout.
export function Spinner({ label }: { label: string }) {
  return (
    <div role="status" className="inline-flex items-center gap-[var(--spacing-12)]">
      <span
        aria-hidden="true"
        className="h-[18px] w-[18px] animate-spin rounded-full border-2 border-(--color-hairline) border-t-(--color-teal)"
      />
      <span className="text-[length:var(--text-nav-label)] text-(--color-ash)">{label}</span>
    </div>
  );
}
