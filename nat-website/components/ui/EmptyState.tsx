type EmptyStateProps = {
  label: string; // labels the <section> for assistive tech
  heading: string; // the one-line explanation of why the view is empty
  action?: { label: string; onClick: () => void };
  /** Set when this is a dynamically-produced no-results state (e.g. search) — announces via
   *  role="status" without moving focus, per spec. */
  announce?: boolean;
};

export function EmptyState({ label, heading, action, announce = false }: EmptyStateProps) {
  return (
    <section
      aria-label={label}
      role={announce ? "status" : undefined}
      className="flex flex-col items-center gap-[var(--spacing-12)] py-[var(--spacing-60)] text-center"
    >
      <svg
        aria-hidden="true"
        viewBox="0 0 24 24"
        className="h-8 w-8 text-(--color-ash)"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.5"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          d="M3 7.5 12 3l9 4.5M3 7.5v9L12 21l9-4.5v-9M3 7.5 12 12m0 0 9-4.5M12 12v9"
        />
      </svg>
      <p className="text-[length:var(--text-nav-label)] text-(--color-ash)">{heading}</p>
      {action && (
        <button
          type="button"
          onClick={action.onClick}
          className="rounded-(--radius-button) bg-(--color-teal) px-[var(--spacing-18)] py-[var(--spacing-12)] text-[length:var(--text-nav-label)] font-medium uppercase tracking-[0.025em] text-(--color-void) transition-opacity hover:opacity-90"
        >
          {action.label}
        </button>
      )}
    </section>
  );
}
