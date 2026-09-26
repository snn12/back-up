import { useTranslations } from "next-intl";

const SERVICE_KEYS = ["nfc", "qr", "website"] as const;

export default function Services() {
  const t = useTranslations("services");

  return (
    <section id="services" className="mx-auto max-w-[1280px] px-[var(--spacing-24)] py-[var(--spacing-96)]">
      <h2 className="max-w-[600px] text-[length:var(--text-heading-sm)] font-normal tracking-[-0.02em] text-(--color-bone)">
        {t("heading")}
      </h2>
      <div className="mt-[var(--spacing-60)] grid grid-cols-1 gap-[var(--spacing-36)] md:grid-cols-3">
        {SERVICE_KEYS.map((key) => (
          <div key={key} className="flex flex-col gap-[var(--spacing-12)]">
            <h3 className="text-[length:var(--text-heading-xs)] font-normal text-(--color-bone)">
              {t(`${key}.title`)}
            </h3>
            <p className="text-[length:var(--text-body)] font-light text-(--color-silver)">
              {t(`${key}.description`)}
            </p>
          </div>
        ))}
      </div>
    </section>
  );
}
