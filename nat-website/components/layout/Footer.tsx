import { useTranslations } from "next-intl";
import { Link } from "@/i18n/navigation";

const SOCIAL_LINKS = [{ label: "Instagram", href: "https://instagram.com/new_age_techno" }];

export default function Footer() {
  const t = useTranslations("footer");

  return (
    <footer className="border-t border-(--color-hairline)">
      <div className="mx-auto flex max-w-[1280px] flex-col gap-[var(--spacing-24)] px-[var(--spacing-24)] py-[var(--spacing-60)] md:flex-row md:items-start md:justify-between">
        <div className="flex max-w-[360px] flex-col gap-[var(--spacing-12)]">
          <span className="text-[length:var(--text-heading-2xs)] font-medium text-(--color-bone)">NAT</span>
          <p className="text-[length:var(--text-nav-label)] text-(--color-ash)">{t("description")}</p>
        </div>

        <div className="flex flex-col gap-[var(--spacing-12)]">
          <div className="flex gap-[var(--spacing-18)]">
            {SOCIAL_LINKS.map((social) => (
              <a
                key={social.href}
                href={social.href}
                target="_blank"
                rel="noreferrer"
                className="text-[length:var(--text-nav-label)] text-(--color-ash) hover:text-(--color-bone)"
              >
                {social.label}
              </a>
            ))}
          </div>
          <a
            href="tel:+994000000000"
            className="text-[length:var(--text-nav-label)] text-(--color-ash) hover:text-(--color-bone)"
          >
            +994 00 000 00 00
          </a>
          <a
            href="mailto:info@nat.example"
            className="text-[length:var(--text-nav-label)] text-(--color-ash) hover:text-(--color-bone)"
          >
            info@nat.example
          </a>
        </div>

        <div className="flex flex-col gap-[var(--spacing-12)]">
          <Link href="/login" className="text-[length:var(--text-caption)] text-(--color-ash) hover:text-(--color-bone)">
            {t("adminLogin")}
          </Link>
          <p className="text-[length:var(--text-caption)] text-(--color-silver)">
            © {new Date().getFullYear()} NAT — New Age Technology. {t("copyright")}
          </p>
        </div>
      </div>
    </footer>
  );
}
