import { NextResponse } from "next/server";
import { z } from "zod";
import { prisma } from "@/lib/db";
import { contactSubmissionSchema } from "@/lib/validation/contact";
import { sendContactNotification } from "@/lib/email";
import { rateLimit } from "@/lib/rate-limit";

// FR-016/Edge Cases: 5 submissions per 10 minutes per client IP.
const SUBMIT_LIMIT = 5;
const SUBMIT_WINDOW_MS = 10 * 60 * 1000;

export async function POST(request: Request) {
  const ip = request.headers.get("x-forwarded-for") ?? "unknown";
  const { ok } = rateLimit(`contact:${ip}`, SUBMIT_LIMIT, SUBMIT_WINDOW_MS);
  if (!ok) {
    return NextResponse.json({ ok: false, errors: { _form: "Too many requests" } }, { status: 429 });
  }

  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ ok: false, errors: { _form: "Invalid request body" } }, { status: 400 });
  }

  const result = contactSubmissionSchema.safeParse(body);
  if (!result.success) {
    const errors: Record<string, string> = {};
    const tree = z.treeifyError(result.error);
    if (tree.errors[0]) errors._form = tree.errors[0];
    for (const [field, detail] of Object.entries(tree.properties ?? {})) {
      const message = detail?.errors?.[0];
      if (message) errors[field] = message;
    }
    return NextResponse.json({ ok: false, errors }, { status: 400 });
  }

  try {
    const submission = await prisma.contactSubmission.create({
      data: result.data,
    });

    // Failure here must never block persistence or the visitor-facing success response.
    const sent = await sendContactNotification(result.data);
    if (sent) {
      await prisma.contactSubmission.update({
        where: { id: submission.id },
        data: { emailNotificationSent: true },
      });
    }

    return NextResponse.json({ ok: true }, { status: 201 });
  } catch (error) {
    console.error("POST /api/contact failed:", error);
    return NextResponse.json({ ok: false, errors: { _form: "Unexpected error" } }, { status: 500 });
  }
}
