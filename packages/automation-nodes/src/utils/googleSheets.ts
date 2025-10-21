import { getGoogleAccessToken } from './googleAuth';

const SHEETS_API = 'https://sheets.googleapis.com/v4';
const SHEETS_SCOPES = ['https://www.googleapis.com/auth/spreadsheets'];

export async function sheetsAppend(spreadsheetId: string, rangeA1: string, values: any[][], valueInputOption: 'RAW'|'USER_ENTERED'='RAW') {
  const token = await getGoogleAccessToken(SHEETS_SCOPES);
  const url = `${SHEETS_API}/spreadsheets/${spreadsheetId}/values/${encodeURIComponent(rangeA1)}:append?valueInputOption=${valueInputOption}`;
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
    body: JSON.stringify({ values }),
  } as any);
  if (!res.ok) throw new Error(`Sheets append failed: ${res.status} ${res.statusText} - ${await res.text()}`);
  return res.json();
}

export async function sheetsRead(spreadsheetId: string, rangeA1: string) {
  const token = await getGoogleAccessToken(SHEETS_SCOPES);
  const url = `${SHEETS_API}/spreadsheets/${spreadsheetId}/values/${encodeURIComponent(rangeA1)}`;
  const res = await fetch(url, { headers: { 'Authorization': `Bearer ${token}` } } as any);
  if (!res.ok) throw new Error(`Sheets read failed: ${res.status} ${res.statusText} - ${await res.text()}`);
  return res.json();
}
