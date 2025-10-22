import { bridgeSwap } from "./samples/bridge.swap.js";
import { sheetsToS3 } from "./samples/sheets.to.s3.js";
import { onchainHashRecord } from "./samples/onchain.hashRecord.js";

type Fn = (params: Record<string, any>) => Promise<any>;

const REGISTRY: Record<string, Fn> = {
  "bridge.swap": bridgeSwap,
  "sheets.to.s3": sheetsToS3,
  "onchain.hashRecord": onchainHashRecord
};

export function resolveNode(name: string): Fn {
  const fn = REGISTRY[name];
  if (!fn) throw new Error(`Node not found: ${name}`);
  return fn;
}
