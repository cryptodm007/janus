import { google } from "googleapis";

type Creds = { clientEmail: string; privateKey: string };
type ReadReq = { spreadsheetId: string; range: string; credentials: Creds };

export async function sheetsRead(req: ReadReq) {
  const jwt = new google.auth.JWT(
    req.credentials.clientEmail,
    undefined,
    req.credentials.privateKey,
    ["https://www.googleapis.com/auth/spreadsheets.readonly"]
  );
  const sheets = google.sheets({ version: "v4", auth: jwt });
  const resp = await sheets.spreadsheets.values.get({
    spreadsheetId: req.spreadsheetId,
    range: req.range
  });
  return resp.data;
}
