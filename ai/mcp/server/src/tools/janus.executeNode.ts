import axios from "axios";
import { ExecuteNodeInput } from "../schema.js";

export async function executeNode(input: unknown) {
  const params = ExecuteNodeInput.parse(input);
  const url = process.env.JANUS_ACTIONS_URL || "http://localhost:7440";
  const { data } = await axios.post(`${url}/ai/actions/execute`, params, {
    headers: { "x-janus-key": process.env.JANUS_API_KEY || "dev" },
    timeout: 15000
  });
  return data;
}
