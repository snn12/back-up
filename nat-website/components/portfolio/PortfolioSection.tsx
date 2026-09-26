import { getTranslations, getLocale } from "next-intl/server";
import { prisma } from "@/lib/db";
import { localizeText } from "@/lib/i18n-content";
import PortfolioCarousel, { type PortfolioCardData } from "./PortfolioCarousel";

export default async function PortfolioSection() {
  const t = await getTranslations("portfolio");
  const locale = await getLocale();

  let items: PortfolioCardData[] = [];
  try {
    const entries = await prisma.portfolioEntry.findMany({
      where: { isActive: true },
      orderBy: { displayOrder: "asc" },
    });
    items = entries.map((entry) => ({
      id: entry.id,
      name: entry.name,
      roleDescription: localizeText(entry.roleDescription, locale),
      imageUrl: entry.imageUrl,
      externalUrl: entry.externalUrl,
    }));
  } catch (error) {
    // Database not yet configured/reachable — render the empty state rather than crash
    // the whole page (see quickstart.md Scenario 3's empty-state expectations).
    console.error("PortfolioSection: failed to load portfolio entries:", error);
  }

  return (
    <section id="portfolio" className="mx-auto max-w-[1280px] px-[var(--spacing-24)] py-[var(--spacing-96)]">
      <h2 className="text-[length:var(--text-heading-sm)] font-normal tracking-[-0.02em] text-(--color-bone)">
        {t("heading")}
      </h2>
      <div className="mt-[var(--spacing-36)]">
        <PortfolioCarousel items={items} />
      </div>
    </section>
  );
}
