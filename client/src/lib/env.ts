import { z } from "zod";

const envSchema = z.object({
  NODE_ENV: z.enum(["development", "test", "production"]).default("development"),
  PORT: z.coerce.number().default(5000),
  NEXT_PUBLIC_APP_URL: z.string().url().default("http://localhost:5000"),
  NEXT_PUBLIC_API_URL: z.string().optional(),
  NEXT_PUBLIC_SERVER_URL: z.string().url().default("http://localhost:3000"),
});

const parseEnv = () => {
  const result = envSchema.safeParse({
    NODE_ENV: process.env.NODE_ENV,
    PORT: process.env.PORT || 5000,
    NEXT_PUBLIC_APP_URL: process.env.NEXT_PUBLIC_APP_URL || "http://localhost:5000",
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL,
    NEXT_PUBLIC_SERVER_URL: process.env.NEXT_PUBLIC_SERVER_URL || "http://localhost:3000",
  });

  if (!result.success) {
    console.error("Invalid environment variables:", result.error.flatten().fieldErrors);
    throw new Error("Invalid environment variables");
  }

  return result.data;
};

export const env = parseEnv();

