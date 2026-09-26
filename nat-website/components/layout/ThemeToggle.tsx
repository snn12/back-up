"use client";

import { useEffect, useState } from "react";
import { useTranslations } from "next-intl";
import { applyTheme, getStoredTheme, setStoredTheme, type Theme } from "@/lib/theme";

function getSystemTheme(): Theme {
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

export default function ThemeToggle() {
  const t = useTranslations("theme");
  const [theme, setTheme] = useState<Theme | null>(null);

  useEffect(() => {
    setTheme(getStoredTheme() ?? getSystemTheme());
  }, []);

  function toggle() {
    const next: Theme = (theme ?? getSystemTheme()) === "dark" ? "light" : "dark";
    setTheme(next);
    setStoredTheme(next);
    applyTheme(next);
  }

  const isDark = (theme ?? "dark") === "dark";

  return (
    <button
      type="button"
      onClick={toggle}
      aria-pressed={isDark}
      aria-label={t("toggle")}
      className="rounded-(--radius-button) border border-(--color-hairline) px-[var(--spacing-12)] py-[var(--spacing-6)] text-[length:var(--text-nav-label)] text-(--color-ash) transition-opacity hover:opacity-70"
    >
      {isDark ? t("light") : t("dark")}
    </button>
  );
}
