const SID = process.env.TWILIO_ACCOUNT_SID || '';
const TOKEN = process.env.TWILIO_AUTH_TOKEN || '';
const API = `https://api.twilio.com/2010-04-01/Accounts`;

export async function twilioSendMessage(from: string, to: string, body: string, messagingServiceSid?: string, mediaUrl?: string) {
  if (!SID || !TOKEN) throw new Error('Missing TWILIO_ACCOUNT_SID or TWILIO_AUTH_TOKEN');
  if (!to || (!from && !messagingServiceSid)) throw new Error('to and (from or messagingServiceSid) are required');

  const form = new URLSearchParams();
  if (from) form.set('From', from);
  if (messagingServiceSid) form.set('MessagingServiceSid', messagingServiceSid);
  form.set('To', to);
  form.set('Body', body || '');
  if (mediaUrl) form.set('MediaUrl', mediaUrl);

  const res = await fetch(`${API}/${SID}/Messages.json`, {
    method: 'POST',
    headers: { 'Authorization': 'Basic ' + Buffer.from(`${SID}:${TOKEN}`).toString('base64'),
               'Content-Type': 'application/x-www-form-urlencoded' },
    body: form.toString(),
  } as any);

  if (!res.ok) throw new Error(`Twilio sendMessage failed: ${res.status} ${res.statusText} - ${await res.text()}`);
  return res.json();
}
