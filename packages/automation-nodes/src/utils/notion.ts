const API = process.env.NOTION_API_BASE || 'https://api.notion.com/v1';
const KEY = process.env.NOTION_API_KEY || '';
const VERSION = process.env.NOTION_VERSION || '2022-06-28';

export async function notionCreatePage(databaseId: string, properties: any, children?: any[]) {
  if (!KEY) throw new Error('Missing NOTION_API_KEY');
  if (!databaseId) throw new Error('databaseId required');

  const body = { parent: { database_id: databaseId }, properties, ...(children ? { children } : {}) };

  const res = await fetch(`${API}/pages`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${KEY}`,
      'Content-Type': 'application/json',
      'Notion-Version': VERSION,
    },
    body: JSON.stringify(body),
  } as any);

  if (!res.ok) throw new Error(`Notion create page failed: ${res.status} ${res.statusText} - ${await res.text()}`);
  return res.json();
}
