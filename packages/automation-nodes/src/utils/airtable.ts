// Cliente mínimo para Airtable (REST).
// Necessita: AIRTABLE_API_KEY, AIRTABLE_BASE_ID.
// Versão REST v0 via endpoints: https://api.airtable.com/v0/{baseId}/{tableName}
const API = process.env.AIRTABLE_API_BASE || 'https://api.airtable.com/v0';
const KEY = process.env.AIRTABLE_API_KEY || '';
const BASE = process.env.AIRTABLE_BASE_ID || '';

function url(baseId: string, table: string, query?: Record<string, string>) {
  const u = new URL(`${API.replace(/\/+$/, '')}/${baseId}/${encodeURIComponent(table)}`);
  if (query) for (const [k, v] of Object.entries(query)) u.searchParams.set(k, v);
  return u.toString();
}

export async function airtableList(table: string, opts?: { filterByFormula?: string; maxRecords?: number; pageSize?: number; view?: string }) {
  if (!KEY) throw new Error('Missing AIRTABLE_API_KEY');
  const res = await fetch(url(BASE, table, {
    ...(opts?.filterByFormula ? { filterByFormula: opts.filterByFormula } : {}),
    ...(opts?.maxRecords ? { maxRecords: String(opts.maxRecords) } : {}),
    ...(opts?.pageSize ? { pageSize: String(opts.pageSize) } : {}),
    ...(opts?.view ? { view: opts.view } : {}),
  }), {
    headers: { 'Authorization': `Bearer ${KEY}` },
  } as any);

  if (!res.ok) throw new Error(`Airtable list failed: ${res.status} ${res.statusText} - ${await res.text()}`);
  return res.json();
}

export async function airtableCreate(table: string, records: any[]) {
  if (!KEY) throw new Error('Missing AIRTABLE_API_KEY');
  const res = await fetch(url(BASE, table), {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${KEY}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ records }),
  } as any);

  if (!res.ok) throw new Error(`Airtable create failed: ${res.status} ${res.statusText} - ${await res.text()}`);
  return res.json();
}

export async function airtableUpdate(table: string, records: any[], typecast = false) {
  if (!KEY) throw new Error('Missing AIRTABLE_API_KEY');
  const res = await fetch(url(BASE, table), {
    method: 'PATCH',
    headers: {
      'Authorization': `Bearer ${KEY}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ records, typecast }),
  } as any);

  if (!res.ok) throw new Error(`Airtable update failed: ${res.status} ${res.statusText} - ${await res.text()}`);
  return res.json();
}
