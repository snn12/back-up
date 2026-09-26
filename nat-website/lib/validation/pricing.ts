import { z } from "zod";

const translatableText = z.object({
  az: z.string().trim().min(1),
  en: z.string().trim().optional(),
  ru: z.string().trim().optional(),
});

const translatableFeatureList = z.object({
  az: z.array(z.string().trim().min(1)).min(1),
  en: z.array(z.string().trim().min(1)).optional(),
  ru: z.array(z.string().trim().min(1)).optional(),
});

export const pricingPlanSchema = z.object({
  tierName: translatableText,
  price: z.number().nonnegative(),
  currency: z.string().trim().min(1).default("AZN"),
  billingPeriod: z.string().trim().optional(),
  features: translatableFeatureList,
  displayOrder: z.number().int().default(0),
  isFeatured: z.boolean().default(false),
});

export const pricingPlanUpdateSchema = pricingPlanSchema.partial();

export type PricingPlanInput = z.infer<typeof pricingPlanSchema>;
export type PricingPlanUpdateInput = z.infer<typeof pricingPlanUpdateSchema>;
