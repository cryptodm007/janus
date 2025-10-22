import { z } from "zod";

export const ExecuteNodeInput = z.object({
  node: z.string(),
  params: z.record(z.any())
});

export const ReadSheetInput = z.object({
  spreadsheetId: z.string(),
  range: z.string()
});

export const S3PutInput = z.object({
  bucket: z.string(),
  key: z.string(),
  content: z.string(),
  contentType: z.string().optional()
});

export const StripeChargeInput = z.object({
  amount: z.number().positive(),
  currency: z.string().min(3),
  source: z.string(), // token ou payment method id (demo)
  metadata: z.record(z.string()).optional()
});
