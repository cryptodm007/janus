import { ReadSheetInput } from "../schema.js";
import { sheetsRead } from "../../../../packages/connectors/google/sheets.js";

export async function readSheet(input: unknown) {
  const p = ReadSheetInput.parse(input);
  return sheetsRead({
    spreadsheetId: p.spreadsheetId,
    range: p.range,
    credentials: {
      clientEmail: process.env.GOOGLE_CLIENT_EMAIL || "",
      privateKey: (process.env.GOOGLE_PRIVATE_KEY || "").replace(/\\n/g, "\n")
    }
  });
}
