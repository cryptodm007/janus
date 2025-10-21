// Cliente mínimo para Discord (REST). Sem terceiros.
const API = process.env.DISCORD_API_BASE || 'https://discord.com/api/v10';
const BOT = process.env.DISCORD_BOT_TOKEN || '';

export type DiscordMessageOptions = {
  channelId: string;
  content?: string;
  embeds?: any[];
  components?: any[];
  tts?: boolean;
};

export async function discordSendMessage(opts: DiscordMessageOptions) {
  if (!BOT) throw new Error('Missing DISCORD_BOT_TOKEN env var');
  if (!opts.channelId) throw new Error('discordSendMessage: channelId required');

  const res = await fetch(`${API}/channels/${opts.channelId}/messages`, {
    method: 'POST',
    headers: {
      'Authorization': `Bot ${BOT}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      content: opts.content ?? '',
      embeds: opts.embeds,
      components: opts.components,
      tts: !!opts.tts,
    }),
  } as any);

  if (!res.ok) {
    const text = await res.text().catch(() => '');
    throw new Error(`Discord message failed: ${res.status} ${res.statusText} - ${text}`);
  }
  return res.json();
}

export async function discordWebhookSend(url: string, body: any) {
  if (!url) throw new Error('discordWebhookSend: webhook url required');
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body || {}),
  } as any);

  if (!res.ok) {
    const text = await res.text().catch(() => '');
    throw new Error(`Discord webhook failed: ${res.status} ${res.statusText} - ${text}`);
  }
  try { return await res.json(); } catch { return await res.text(); }
}
