import { google } from "googleapis";

type Creds = { clientEmail: string; privateKey: string };
type ReadReq = { spreadsheetId: string; range: string; credentials: Creds };
type AppendReq = { spreadsheetId: string; range: string; values: any[][]; credentials: Creds };

function client(creds: Creds) {
  const jwt = new google.auth.JWT(
    creds.clientEmail,
    undefined,
    creds.privateKey,
    ["https://www.googleapis.com/auth/spreadsheets"]
  );
  return google.sheets({ version: "v4", auth: jwt });
}

async function withRetry<T>(fn: () => Promise<T>, tries = 3): Promise<T> {
  let lastErr: any;
  for (let i = 0; i < tries; i++) {
    try { return await fn(); } catch (e) { lastErr = e; await new Promise(r => setTimeout(r, 300 * (i + 1))); }
  }
  throw lastErr;
}

export async function sheetsRead(req: ReadReq) {
  const s = client(req.credentials);
  return withRetry(async () => {
    const resp = await s.spreadsheets.values.get({ spreadsheetId: req.spreadsheetId, range: req.range });
    return resp.data;
  });
}

export async function sheetsAppend(req: AppendReq) {
  const s = client(req.credentials);
  return withRetry(async () => {
    const resp = await s.spreadsheets.values.append({
      spreadsheetId: req.spreadsheetId,
      range: req.range,
      valueInputOption: "USER_ENTERED",
      requestBody: { values: req.values }
    });
    return { updatedRange: resp.data.updates?.updatedRange };
  });
}
