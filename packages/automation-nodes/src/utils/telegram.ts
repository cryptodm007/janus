const BOT_TOKEN = process.env.TELEGRAM_BOT_TOKEN || '';
const API = BOT_TOKEN ? `https://api.telegram.org/bot${BOT_TOKEN}` : '';

export async function telegramSendMessage(chatId: string, text: string, parseMode?: string, disableWebPagePreview?: boolean) {
  if (!BOT_TOKEN) throw new Error('Missing TELEGRAM_BOT_TOKEN');
  if (!chatId) throw new Error('chatId required');

  const res = await fetch(`${API}/sendMessage`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ chat_id: chatId, text, parse_mode: parseMode, disable_web_page_preview: !!disableWebPagePreview }),
  } as any);

  if (!res.ok) throw new Error(`Telegram sendMessage failed: ${res.status} ${res.statusText} - ${await res.text()}`);
  return res.json();
}
