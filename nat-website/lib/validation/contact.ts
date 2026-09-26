import { z } from "zod";

// Mirrors specs/001-nat-corporate-website/data-model.md's ContactSubmission validation rules.
export const contactSubmissionSchema = z.object({
  firstName: z.string().trim().min(1).max(80),
  lastName: z.string().trim().min(1).max(80),
  email: z.string().trim().email(),
  phoneCountryCode: z.string().trim().min(1).max(6),
  phoneNumber: z.string().trim().min(1).max(20),
  message: z
    .string()
    .trim()
    .min(1)
    .max(2000)
    // Strip any HTML/script tags before the value ever reaches storage or the admin
    // dashboard that later renders it (FR-016).
    .transform((value) => value.replace(/<[^>]*>/g, "")),
  consentAccepted: z.literal(true, {
    error: "Məxfilik siyasətinə razılıq vermək lazımdır.",
  }),
});

export type ContactSubmissionInput = z.infer<typeof contactSubmissionSchema>;
