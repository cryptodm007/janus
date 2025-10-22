import { createHmac } from "crypto";
export function sign(payload: string, secret: string) {
  return createHmac("sha256", secret).update(payload).digest("hex");
}
