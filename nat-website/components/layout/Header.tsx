"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { Link } from "@/i18n/navigation";
import ThemeToggle from "./ThemeToggle";
import LanguageSwitcher from "./LanguageSwitcher";

const NAV_ITEMS = [
  { key: "home", href: "/" },
  { key: "services", href: "/#services" },
  { key: "portfolio", href: "/#portfolio" },
  { key: "pricing", href: "/#pricing" },
  { key: "about", href: "/#about" },
  { key: "faq", href: "/#faq" },
  { key: "contact", href: "/#contact" },
] as const;

export default function Header() {
  const t = useTranslations("nav");
  const [open, setOpen] = useState(false);

  return (
    <header className="sticky top-0 z-40 border-b border-(--color-hairline) bg-(--color-void)/90 backdrop-blur">
      <div className="mx-auto flex max-w-[1280px] items-center justify-between px-[var(--spacing-24)] py-[var(--spacing-18)]">
        <Link href="/" className="text-[length:var(--text-heading-2xs)] font-medium text-(--color-bone)">
          NAT
        </Link>

        {/* Desktop nav — hidden below 999px, replaced by the hamburger button. */}
        <nav aria-label="Primary" className="hidden items-center gap-[var(--spacing-30)] lg:flex">
          {NAV_ITEMS.map((item) => (
            <Link
              key={item.key}
              href={item.href}
              className="text-[length:var(--text-nav-label)] uppercase tracking-[0.025em] text-(--color-ash) transition-opacity hover:text-(--color-bone)"
            >
              {t(item.key)}
            </Link>
          ))}
          <ThemeToggle />
          <LanguageSwitcher />
        </nav>

        <button
          type="button"
          className="grid h-11 w-11 place-items-center rounded-full border border-(--color-hairline) lg:hidden"
          aria-label={t("menu")}
          aria-expanded={open}
          aria-controls="mobile-nav"
          onClick={() => setOpen((value) => !value)}
        >
          <svg viewBox="0 0 24 24" className="h-5 w-5" aria-hidden="true">
            <rect x="3" y="7" width="18" height="1.7" rx="0.85" fill="currentColor" />
            <rect x="3" y="15" width="18" height="1.7" rx="0.85" fill="currentColor" />
          </svg>
        </button>
      </div>

      {open && (
        <nav
          id="mobile-nav"
          aria-label="Primary"
          className="flex flex-col gap-[var(--spacing-18)] border-t border-(--color-hairline) px-[var(--spacing-24)] py-[var(--spacing-24)] lg:hidden"
        >
          {NAV_ITEMS.map((item) => (
            <Link
              key={item.key}
              href={item.href}
              onClick={() => setOpen(false)}
              className="text-[length:var(--text-body)] text-(--color-ash)"
            >
              {t(item.key)}
            </Link>
          ))}
          <div className="flex items-center gap-[var(--spacing-18)] pt-[var(--spacing-12)]">
            <ThemeToggle />
            <LanguageSwitcher />
          </div>
        </nav>
      )}
    </header>
  );
}
