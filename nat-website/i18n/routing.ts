import { defineRouting } from "next-intl/routing";

// FR-022: Azerbaijani, English, Russian; Azerbaijani is the default/fallback locale (FR-025).
export const routing = defineRouting({
  locales: ["az", "en", "ru"],
  defaultLocale: "az",
});

export type Locale = (typeof routing.locales)[number];
