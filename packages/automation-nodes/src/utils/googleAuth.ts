import crypto from 'crypto';

const GOOGLE_TOKEN_URL = 'https://oauth2.googleapis.com/token';

function b64url(input: Buffer | string) {
  return Buffer.from(input).toString('base64').replace(/=/g, '').replace(/\+/g, '-').replace(/\//g, '_');
}

export async function getGoogleAccessToken(scopes: string[]): Promise<string> {
  const clientEmail = process.env.GOOGLE_SERVICE_ACCOUNT_EMAIL || '';
  let privateKey = process.env.GOOGLE_SERVICE_ACCOUNT_PRIVATE_KEY || '';
  if (!clientEmail || !privateKey) {
    throw new Error('Missing GOOGLE_SERVICE_ACCOUNT_EMAIL or GOOGLE_SERVICE_ACCOUNT_PRIVATE_KEY');
  }
  // Permite chave vinda com \n escapado
  privateKey = privateKey.replace(/\\n/g, '\n');

  const iat = Math.floor(Date.now() / 1000);
  const exp = iat + 3600; // 1h
  const header = { alg: 'RS256', typ: 'JWT' };
  const claim = {
    iss: clientEmail,
    scope: scopes.join(' '),
    aud: GOOGLE_TOKEN_URL,
    exp,
    iat,
  };

  const toSign = `${b64url(JSON.stringify(header))}.${b64url(JSON.stringify(claim))}`;
  const signer = crypto.createSign('RSA-SHA256');
  signer.update(toSign);
  const signature = signer.sign(privateKey);
  const jwt = `${toSign}.${b64url(signature)}`;

  const res = await fetch(GOOGLE_TOKEN_URL, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: new URLSearchParams({
      grant_type: 'urn:ietf:params:oauth:grant-type:jwt-bearer',
      assertion: jwt,
    }).toString(),
  } as any);

  if (!res.ok) {
    throw new Error(`Google token fetch failed: ${res.status} ${res.statusText} - ${await res.text()}`);
  }
  const data = await res.json();
  return data.access_token as string;
}
