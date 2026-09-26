export type PricingCardData = {
  id: string;
  tierName: string;
  price: number;
  currency: string;
  billingPeriod: string | null;
  features: string[];
  isFeatured: boolean;
};

export default function PricingGrid({ plans }: { plans: PricingCardData[] }) {
  return (
    <div className="grid grid-cols-1 gap-[var(--spacing-24)] md:grid-cols-2">
      {plans.map((plan) => (
        <div
          key={plan.id}
          className={
            "flex flex-col gap-[var(--spacing-18)] rounded-(--radius-card) border p-[var(--spacing-24)] " +
            (plan.isFeatured ? "border-(--color-teal)" : "border-(--color-hairline)")
          }
        >
          <h3 className="text-[length:var(--text-heading-xs)] font-normal text-(--color-bone)">{plan.tierName}</h3>
          <p className="text-[length:var(--text-heading-sm)] font-normal text-(--color-bone)">
            {plan.price} {plan.currency}
            {plan.billingPeriod && (
              <span className="text-[length:var(--text-nav-label)] font-light text-(--color-ash)"> / {plan.billingPeriod}</span>
            )}
          </p>
          <ul className="flex flex-col gap-[var(--spacing-6)]">
            {plan.features.map((feature) => (
              <li key={feature} className="text-[length:var(--text-nav-label)] font-light text-(--color-silver)">
                {feature}
              </li>
            ))}
          </ul>
        </div>
      ))}
    </div>
  );
}
