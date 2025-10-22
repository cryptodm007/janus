import { Router } from "express";

const r = Router();

r.get("/:id", async (req, res) => {
  // TODO: consultar AgentRegistry on-chain
  res.json({ id: req.params.id, stake: "1000 JNS", reputation: 0, version: "0.1.0" });
});

r.post("/register", async (req, res) => {
  // TODO: registrar agente (on-chain + off-chain registry)
  res.json({ ok: true, id: req.body?.id || "agent_" + Date.now() });
});

export default r;
