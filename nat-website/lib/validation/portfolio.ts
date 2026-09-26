import { z } from "zod";

// Translatable text: az is required (fallback locale, FR-025), en/ru optional.
const translatableText = z.object({
  az: z.string().trim().min(1),
  en: z.string().trim().optional(),
  ru: z.string().trim().optional(),
});

const urlField = z.string().trim().url().optional().or(z.literal("").transform(() => undefined));

export const portfolioEntrySchema = z.object({
  name: z.string().trim().min(1).max(120),
  roleDescription: translatableText,
  bio: translatableText,
  imageUrl: z.string().trim().min(1),
  externalUrl: urlField,
  socialLink: urlField,
  isActive: z.boolean().default(true),
  displayOrder: z.number().int().default(0),
});

export const portfolioEntryUpdateSchema = portfolioEntrySchema.partial();

export type PortfolioEntryInput = z.infer<typeof portfolioEntrySchema>;
export type PortfolioEntryUpdateInput = z.infer<typeof portfolioEntryUpdateSchema>;
