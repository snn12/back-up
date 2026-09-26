import { useTranslations } from "next-intl";
import ParticleField from "@/components/hero/ParticleField";
import ScrambleText from "@/components/hero/ScrambleText";
import Services from "@/components/sections/Services";
import PortfolioSection from "@/components/portfolio/PortfolioSection";
import PricingSection from "@/components/pricing/PricingSection";
import About from "@/components/sections/About";
import Faq from "@/components/sections/Faq";
import ContactForm from "@/components/contact/ContactForm";

// Signature hero (User Story 5): an animated particle field (structurally carried over from
// the Dala reference's "constellation brain" imagery, re-colored to NAT's teal palette) behind
// the headline, plus a scramble-text reveal on the NEW AGE TECHNOLOGY sub-brand line.
function Hero() {
  const t = useTranslations("hero");

  return (
    <section className="relative flex min-h-screen flex-col items-center justify-center gap-[var(--spacing-24)] overflow-hidden px-[var(--spacing-24)] text-center">
      <ParticleField />
      <div className="relative z-10 flex flex-col items-center gap-[var(--spacing-24)]">
        <h1 className="max-w-[900px] break-words text-[length:var(--text-heading-xs)] font-normal tracking-[-0.02em] text-(--color-bone) sm:text-[length:var(--text-heading)] md:text-[length:var(--text-heading-lg)]">
          {t("tagline")}
        </h1>
        <ScrambleText
          text={t("subbrand")}
          className="text-[length:var(--text-nav-label)] uppercase tracking-[0.1em] text-(--color-silver)"
        />
        <a
          href="#contact"
          className="mt-[var(--spacing-12)] rounded-(--radius-button) bg-(--color-teal) px-[var(--spacing-24)] py-[var(--spacing-18)] text-[length:var(--text-nav-label)] font-semibold uppercase tracking-[0.025em] text-(--color-void) transition-opacity hover:opacity-90"
        >
          {t("cta")}
        </a>
      </div>
    </section>
  );
}

export default function HomePage() {
  return (
    <main>
      <Hero />
      <Services />
      <PortfolioSection />
      <PricingSection />
      <About />
      <Faq />
      <ContactForm />
    </main>
  );
}
