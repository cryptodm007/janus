import { Request, Response, NextFunction } from "express";

export function auth(req: Request, res: Response, next: NextFunction) {
  const key = req.header("x-janus-key");
  if (!key || key !== (process.env.JANUS_API_KEY || "dev")) {
    return res.status(401).json({ error: "unauthorized" });
  }
  next();
}
