// Used when the final content's geometry is already known (e.g. a portfolio card grid) so the
// loading placeholder preserves that shape and the layout doesn't "jump" once data arrives.
export function Skeleton({ className = "" }: { className?: string }) {
  return (
    <div
      aria-hidden="true"
      className={`animate-pulse rounded-(--radius-card) bg-(--color-surface) ${className}`}
    />
  );
}

// Wrap a region that is loading in aria-busy so assistive tech knows content is pending.
export function BusyRegion({
  loading,
  children,
  className = "",
}: {
  loading: boolean;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div aria-busy={loading} className={className}>
      {children}
    </div>
  );
}
