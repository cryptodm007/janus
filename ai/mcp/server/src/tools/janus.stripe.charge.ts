import { StripeChargeInput } from "../schema.js";
import { createCharge } from "../../../../packages/connectors/stripe/payments.js";

export async function stripeCharge(input: unknown) {
  const p = StripeChargeInput.parse(input);
  return createCharge({
    amount: p.amount,
    currency: p.currency,
    source: p.source,
    metadata: p.metadata
  });
}
