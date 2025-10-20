#!/usr/bin/env node
// Base CLI (init/status) — placeholder seguro.
// Aceita flags: --network <net> --payload <base64:...> --intent <id>
import { argv, exit } from "node:process";

function parseArgs() {
  const args = { _: [] };
  for (let i = 2; i < argv.length; i++) {
    const a = argv[i];
    if (a.startsWith("--")) {
      const key = a.slice(2);
      const val = argv[i + 1] && !argv[i + 1].startsWith("--") ? argv[++i] : true;
      args[key] = val;
    } else {
      args._.push(a);
    }
  }
  return args;
}

const args = parseArgs();
const cmd = args._[0];

function out(obj, ok = true) {
  console.log(JSON.stringify(obj));
  exit(ok ? 0 : 1);
}

if (cmd === "init") {
  const intentId = args.intent || `intent-${Date.now()}`;
  // TODO: integrar com o submódulo quando houver API/CLI real
  return out({ intentId, txId: `0x${Math.floor(Math.random()*1e16).toString(16)}`, status: "SENT" });
}

if (cmd === "status") {
  const intentId = args.intent || "unknown";
  // placeholder: devolve sempre SENT
  return out({ intentId, status: "SENT" });
}

out({ error: `unknown command: ${cmd}` }, false);
