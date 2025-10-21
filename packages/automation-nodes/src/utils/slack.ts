const API = process.env.SLACK_API_BASE || 'https://slack.com/api';
const BOT = process.env.SLACK_BOT_TOKEN || '';

export async function slackPostMessage(channel: string, text?: string, blocks?: any[], attachments?: any[]) {
  if (!BOT) throw new Error('Missing SLACK_BOT_TOKEN');
  if (!channel) throw new Error('slackPostMessage: channel required');

  const res = await fetch(`${API}/chat.postMessage`, {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${BOT}`, 'Content-Type': 'application/json' },
    body: JSON.stringify({ channel, text: text ?? '', blocks, attachments }),
  } as any);

  if (!res.ok) throw new Error(`Slack chat.postMessage failed: ${res.status} ${res.statusText} - ${await res.text()}`);
  return res.json();
}

export async function slackWebhookSend(url: string, body: any) {
  if (!url) throw new Error('slackWebhookSend: webhook url required');
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body || {}),
  } as any);
  if (!res.ok) throw new Error(`Slack webhook failed: ${res.status} ${res.statusText} - ${await res.text()}`);
  try { return await res.json(); } catch { return await res.text(); }
}
