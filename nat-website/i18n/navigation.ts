import { createNavigation } from "next-intl/navigation";
import { routing } from "./routing";

// Locale-aware Link/redirect/usePathname/useRouter — use these instead of the plain
// Next.js equivalents anywhere a link should stay within the current locale.
export const { Link, redirect, usePathname, useRouter, getPathname } = createNavigation(routing);
