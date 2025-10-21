import crypto from 'crypto';

function hmac(key: Buffer | string, data: string) {
  return crypto.createHmac('sha256', key).update(data, 'utf8').digest();
}
function sha256Hex(data: Buffer | string) {
  return crypto.createHash('sha256').update(data).digest('hex');
}

export type S3PutParams = {
  region: string;
  bucket: string;
  key: string;
  contentType?: string;
  bodyBase64: string;
  acl?: string; // ex: 'public-read'
};

export async function s3PutObject(params: S3PutParams) {
  const accessKey = process.env.AWS_ACCESS_KEY_ID || '';
  const secretKey = process.env.AWS_SECRET_ACCESS_KEY || '';
  if (!accessKey || !secretKey) throw new Error('Missing AWS_ACCESS_KEY_ID or AWS_SECRET_ACCESS_KEY');

  const { region, bucket, key, contentType, bodyBase64, acl } = params;
  const host = `${bucket}.s3.${region}.amazonaws.com`;
  const now = new Date();
  const amzDate = now.toISOString().replace(/[:-]|\.\d{3}/g, '').slice(0, 15) + 'Z'; // YYYYMMDDTHHMMSSZ
  const dateStamp = amzDate.slice(0, 8); // YYYYMMDD

  const body = Buffer.from(bodyBase64, 'base64');
  const payloadHash = sha256Hex(body);

  const canonicalUri = `/${encodeURIComponent(key).replace(/%2F/g, '/')}`;
  const canonicalQueryString = '';
  const canonicalHeaders =
    `host:${host}\n` +
    `x-amz-content-sha256:${payloadHash}\n` +
    `x-amz-date:${amzDate}\n` +
    (acl ? `x-amz-acl:${acl}\n` : '');
  const signedHeaders =
    'host;x-amz-content-sha256;x-amz-date' + (acl ? ';x-amz-acl' : '');

  const canonicalRequest =
    `PUT\n${canonicalUri}\n${canonicalQueryString}\n${canonicalHeaders}\n${signedHeaders}\n${payloadHash}`;

  const algorithm = 'AWS4-HMAC-SHA256';
  const credentialScope = `${dateStamp}/${region}/s3/aws4_request`;
  const stringToSign =
    `${algorithm}\n${amzDate}\n${credentialScope}\n${sha256Hex(canonicalRequest)}`;

  const kDate = hmac('AWS4' + secretKey, dateStamp);
  const kRegion = hmac(kDate, region);
  const kService = hmac(kRegion, 's3');
  const kSigning = hmac(kService, 'aws4_request');
  const signature = crypto.createHmac('sha256', kSigning).update(stringToSign).digest('hex');

  const authHeader =
    `${algorithm} Credential=${accessKey}/${credentialScope}, SignedHeaders=${signedHeaders}, Signature=${signature}`;

  const headers: Record<string, string> = {
    'Authorization': authHeader,
    'x-amz-date': amzDate,
    'x-amz-content-sha256': payloadHash,
    ...(acl ? { 'x-amz-acl': acl } : {}),
    ...(contentType ? { 'Content-Type': contentType } : {}),
    'Content-Length': String(body.length),
  };

  const url = `https://${host}${canonicalUri}`;
  const res = await fetch(url, { method: 'PUT', headers, body } as any);
  if (!res.ok) {
    const text = await res.text().catch(() => '');
    throw new Error(`S3 PUT failed: ${res.status} ${res.statusText} - ${text}`);
  }
  // Em PUT, S3 não retorna JSON — retornamos info mínima.
  return { ok: true, etag: res.headers.get('etag') || null, url };
}
