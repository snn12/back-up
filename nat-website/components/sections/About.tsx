import { useTranslations } from "next-intl";

export default function About() {
  const t = useTranslations("about");

  return (
    <section id="about" className="mx-auto max-w-[1280px] px-[var(--spacing-24)] py-[var(--spacing-96)]">
      <h2 className="max-w-[720px] text-[length:var(--text-heading-sm)] font-normal tracking-[-0.02em] text-(--color-bone)">
        {t("heading")}
      </h2>
      <p className="mt-[var(--spacing-24)] max-w-[65ch] text-[length:var(--text-body)] font-light text-(--color-silver)">
        {t("body")}
      </p>
    </section>
  );
}
