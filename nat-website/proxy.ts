import createIntlMiddleware from "next-intl/middleware";
import { NextResponse, type NextRequest } from "next/server";
import { auth } from "@/lib/auth";
import { routing } from "@/i18n/routing";

// Next.js 16 renamed `middleware.ts` to `proxy.ts` with a `proxy` named export
// (see AGENTS.md / node_modules/next/dist/docs/01-app/02-guides/upgrading/version-16.md).
// This function does two jobs: (1) next-intl locale routing/redirect, (2) gate `/[locale]/admin`
// behind an authenticated session (FR-012) before the locale-routed response is returned.

const intlMiddleware = createIntlMiddleware(routing);

const ADMIN_SEGMENT = /^\/(az|en|ru)\/admin(\/|$)/;

export async function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl;

  if (ADMIN_SEGMENT.test(pathname)) {
    const session = await auth();
    if (!session) {
      const locale = pathname.split("/")[1] || routing.defaultLocale;
      const loginUrl = new URL(`/${locale}/login`, request.url);
      return NextResponse.redirect(loginUrl);
    }
  }

  return intlMiddleware(request);
}

export const config = {
  matcher: ["/((?!api|_next|_vercel|.*\\..*).*)"],
};
