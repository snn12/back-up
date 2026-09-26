"use client";

import { useLocale, useTranslations } from "next-intl";
import { usePathname, useRouter } from "@/i18n/navigation";
import { routing } from "@/i18n/routing";

const LABELS: Record<string, string> = { az: "AZ", en: "EN", ru: "RU" };

export default function LanguageSwitcher() {
  const t = useTranslations("language");
  const locale = useLocale();
  const pathname = usePathname();
  const router = useRouter();

  return (
    <div role="group" aria-label={t("label")} className="flex items-center gap-[var(--spacing-6)]">
      {routing.locales.map((code) => (
        <button
          key={code}
          type="button"
          aria-current={code === locale ? "true" : undefined}
          onClick={() => router.replace(pathname, { locale: code })}
          className={
            "rounded-(--radius-tag) px-[var(--spacing-12)] py-[var(--spacing-6)] text-[length:var(--text-nav-label)] transition-opacity hover:opacity-70 " +
            (code === locale ? "text-(--color-bone)" : "text-(--color-ash)")
          }
        >
          {LABELS[code]}
        </button>
      ))}
    </div>
  );
}
