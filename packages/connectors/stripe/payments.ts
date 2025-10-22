import Stripe from "stripe";

const stripe = new Stripe(process.env.STRIPE_SECRET_KEY || "", { apiVersion: "2024-06-20" });

type ChargeReq = { amount: number; currency: string; source: string; metadata?: Record<string,string> };

export async function createCharge(req: ChargeReq) {
  const cents = Math.round(req.amount * 100);
  const charge = await stripe.charges.create({
    amount: cents,
    currency: req.currency,
    source: req.source,
    metadata: req.metadata
  });
  return { id: charge.id, status: charge.status };
}
