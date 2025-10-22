import express from "express";
import bodyParser from "body-parser";
import { auth } from "./middleware/auth.js";
import actions from "./routes/actions.js";
import agents from "./routes/agents.js";

const app = express();
app.use(bodyParser.json());

app.use("/ai/actions", auth, actions);
app.use("/ai/agents", auth, agents);

const PORT = Number(process.env.AI_API_PORT || 7440);
app.listen(PORT, () => console.log(`[AI-API] listening :${PORT}`));
