import axios from "axios";
export async function onchainHashRecord(input: { data: any }) {
  const url = process.env.JANUS_ACTIONS_URL || "http://localhost:7440";
  const { data } = await axios.post(`${url}/ai/actions/execute`, { node: "onchain.hashRecord", params: input }, {
    headers: { "x-janus-key": process.env.JANUS_API_KEY || "dev" }
  });
  return data;
}
