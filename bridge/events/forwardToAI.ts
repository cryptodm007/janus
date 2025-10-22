import axios from "axios";
import { aiChannel } from "./aiChannel.js";

const HUB = process.env.AI_HUB_URL || "http://localhost:7331";

aiChannel.on("POOL_IMBALANCE_DETECTED", async (payload) => {
  try {
    await axios.post(HUB, { tool: "janus.event.notify", input: { event: "POOL_IMBALANCE_DETECTED", payload } });
    console.log("[Bridge→AI] forwarded", payload);
  } catch (e) {
    console.error("[Bridge→AI] fail", e);
  }
});
