import { Resend } from "resend";
import type { ContactSubmissionInput } from "@/lib/validation/contact";

// Single choke point for outbound email so the provider is swappable (research.md decision).
// Failure here must never block persistence or the visitor-facing success response (FR-024) —
// callers are expected to catch and log, not propagate.
export async function sendContactNotification(submission: ContactSubmissionInput): Promise<boolean> {
  const apiKey = process.env.RESEND_API_KEY;
  const to = process.env.CONTACT_NOTIFICATION_EMAIL;
  if (!apiKey || !to) {
    console.warn("sendContactNotification: RESEND_API_KEY or CONTACT_NOTIFICATION_EMAIL not configured; skipping.");
    return false;
  }

  try {
    const resend = new Resend(apiKey);
    await resend.emails.send({
      from: "NAT Website <noreply@nat.example>",
      to,
      subject: `Yeni əlaqə mesajı — ${submission.firstName} ${submission.lastName}`,
      text: [
        `Ad: ${submission.firstName} ${submission.lastName}`,
        `Email: ${submission.email}`,
        `Telefon: ${submission.phoneCountryCode} ${submission.phoneNumber}`,
        "",
        submission.message,
      ].join("\n"),
    });
    return true;
  } catch (error) {
    console.error("sendContactNotification failed:", error);
    return false;
  }
}
