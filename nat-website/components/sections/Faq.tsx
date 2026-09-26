import { useTranslations } from "next-intl";

type FaqItem = { q: string; a: string };

export default function Faq() {
  const t = useTranslations("faq");
  const items = t.raw("items") as FaqItem[];

  return (
    <section id="faq" className="mx-auto max-w-[1280px] px-[var(--spacing-24)] py-[var(--spacing-96)]">
      <h2 className="text-[length:var(--text-heading-sm)] font-normal tracking-[-0.02em] text-(--color-bone)">
        {t("heading")}
      </h2>

      <div className="mt-[var(--spacing-36)] flex max-w-[720px] flex-col divide-y divide-(--color-hairline)">
        {items.map((item) => (
          // Native <details>/<summary> — shared `name` makes the group exclusive (only one
          // panel open at a time) without any custom aria-expanded wiring (constitution II).
          <details key={item.q} name="faq" className="group py-[var(--spacing-18)]">
            <summary className="flex cursor-pointer list-none items-center justify-between text-[length:var(--text-body)] text-(--color-bone)">
              {item.q}
              <span aria-hidden="true" className="ml-[var(--spacing-12)] text-(--color-ash) group-open:rotate-45">
                +
              </span>
            </summary>
            <p className="mt-[var(--spacing-12)] text-[length:var(--text-nav-label)] font-light text-(--color-silver)">
              {item.a}
            </p>
          </details>
        ))}
      </div>
    </section>
  );
}
