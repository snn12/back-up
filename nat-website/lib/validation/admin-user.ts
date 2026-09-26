import { z } from "zod";

// FR-023: account creation is server-side restricted to an existing admin session;
// this schema only validates shape, the session check happens in the route handler.
export const createAdminUserSchema = z.object({
  email: z.string().trim().email(),
  password: z.string().min(10).max(200),
});

export type CreateAdminUserInput = z.infer<typeof createAdminUserSchema>;
