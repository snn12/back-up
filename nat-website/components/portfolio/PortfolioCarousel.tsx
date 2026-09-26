"use client";

import { useCallback, useEffect, useState } from "react";
import useEmblaCarousel from "embla-carousel-react";
import Image from "next/image";
import { useTranslations } from "next-intl";
import { EmptyState } from "@/components/ui/EmptyState";

export type PortfolioCardData = {
  id: string;
  name: string;
  roleDescription: string;
  imageUrl: string;
  externalUrl: string | null;
};

export default function PortfolioCarousel({ items }: { items: PortfolioCardData[] }) {
  const t = useTranslations("portfolio");
  const [emblaRef, emblaApi] = useEmblaCarousel({ loop: false });
  const [selectedIndex, setSelectedIndex] = useState(0);

  const onSelect = useCallback(() => {
    if (emblaApi) setSelectedIndex(emblaApi.selectedScrollSnap());
  }, [emblaApi]);

  useEffect(() => {
    if (!emblaApi) return;
    onSelect();
    emblaApi.on("select", onSelect);
    return () => {
      emblaApi.off("select", onSelect);
    };
  }, [emblaApi, onSelect]);

  if (items.length === 0) {
    return <EmptyState label={t("heading")} heading={t("empty.heading")} />;
  }

  return (
    <div
      role="region"
      aria-roledescription="carousel"
      aria-label={t("heading")}
      className="relative"
    >
      <div className="overflow-hidden" ref={emblaRef}>
        <div className="flex gap-[var(--spacing-24)]">
          {items.map((item, index) => (
            <div
              key={item.id}
              role="group"
              aria-roledescription="slide"
              aria-label={`${index + 1} of ${items.length}`}
              className="min-w-0 flex-[0_0_100%] md:flex-[0_0_45%]"
            >
              <a
                href={item.externalUrl ?? undefined}
                target={item.externalUrl ? "_blank" : undefined}
                rel={item.externalUrl ? "noreferrer" : undefined}
                className="block"
              >
                <div className="relative aspect-[4/3] overflow-hidden rounded-(--radius-card)">
                  <Image src={item.imageUrl} alt={item.name} fill className="object-cover" />
                </div>
                <p className="mt-[var(--spacing-18)] text-[length:var(--text-caption)] uppercase tracking-[0.025em] text-(--color-teal)">
                  {item.roleDescription}
                </p>
                <h3 className="text-[length:var(--text-heading-xs)] font-normal text-(--color-bone)">
                  {item.name}
                </h3>
              </a>
            </div>
          ))}
        </div>
      </div>

      <div className="mt-[var(--spacing-24)] flex items-center justify-center gap-[var(--spacing-18)]">
        <button
          type="button"
          onClick={() => emblaApi?.scrollPrev()}
          aria-label="Previous"
          className="grid h-10 w-10 place-items-center rounded-full border border-(--color-hairline) text-(--color-ash) hover:text-(--color-bone)"
        >
          ‹
        </button>
        <div className="flex gap-[var(--spacing-6)]">
          {items.map((item, index) => (
            <button
              key={item.id}
              type="button"
              aria-label={`Go to slide ${index + 1}`}
              aria-current={index === selectedIndex}
              onClick={() => emblaApi?.scrollTo(index)}
              className={`h-2 w-2 rounded-full ${index === selectedIndex ? "bg-(--color-teal)" : "bg-(--color-hairline)"}`}
            />
          ))}
        </div>
        <button
          type="button"
          onClick={() => emblaApi?.scrollNext()}
          aria-label="Next"
          className="grid h-10 w-10 place-items-center rounded-full border border-(--color-hairline) text-(--color-ash) hover:text-(--color-bone)"
        >
          ›
        </button>
      </div>
    </div>
  );
}
