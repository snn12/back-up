import { getTranslations, getLocale } from "next-intl/server";
import { prisma } from "@/lib/db";
import { localizeText, localizeList } from "@/lib/i18n-content";
import PricingGrid, { type PricingCardData } from "./PricingGrid";
import { EmptyState } from "@/components/ui/EmptyState";

export default async function PricingSection() {
  const t = await getTranslations("pricing");
  const locale = await getLocale();

  let plans: PricingCardData[] = [];
  try {
    const rows = await prisma.pricingPlan.findMany({ orderBy: { displayOrder: "asc" } });
    plans = rows.map((row) => ({
      id: row.id,
      tierName: localizeText(row.tierName, locale),
      price: Number(row.price),
      currency: row.currency,
      billingPeriod: row.billingPeriod,
      features: localizeList(row.features, locale),
      isFeatured: row.isFeatured,
    }));
  } catch (error) {
    console.error("PricingSection: failed to load pricing plans:", error);
  }

  return (
    <section id="pricing" className="mx-auto max-w-[1280px] px-[var(--spacing-24)] py-[var(--spacing-96)]">
      <h2 className="text-[length:var(--text-heading-sm)] font-normal tracking-[-0.02em] text-(--color-bone)">
        {t("heading")}
      </h2>
      <div className="mt-[var(--spacing-36)]">
        {plans.length > 0 ? (
          <PricingGrid plans={plans} />
        ) : (
          <EmptyState label={t("heading")} heading={t("empty")} />
        )}
      </div>
    </section>
  );
}
