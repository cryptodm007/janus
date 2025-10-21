import { getGoogleAccessToken } from './googleAuth';

const DRIVE_API = 'https://www.googleapis.com/drive/v3';
const DRIVE_UPLOAD = 'https://www.googleapis.com/upload/drive/v3/files';

const DRIVE_SCOPES = [
  'https://www.googleapis.com/auth/drive.file',
];

export async function driveCreateFolder(name: string, parentId?: string) {
  const token = await getGoogleAccessToken(DRIVE_SCOPES);
  const body: any = { name, mimeType: 'application/vnd.google-apps.folder' };
  if (parentId) body.parents = [parentId];

  const res = await fetch(`${DRIVE_API}/files`, {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  } as any);

  if (!res.ok) throw new Error(`Drive create folder failed: ${res.status} ${res.statusText} - ${await res.text()}`);
  return res.json();
}

export async function driveUploadFile(params: {
  name: string;
  mimeType: string;
  contentBase64: string;
  parentId?: string;
}) {
  const token = await getGoogleAccessToken(DRIVE_SCOPES);
  const boundary = 'janusboundary' + Date.now();
  const meta: any = { name: params.name };
  if (params.parentId) meta.parents = [params.parentId];

  const metaPart =
    `--${boundary}\r\n` +
    `Content-Type: application/json; charset=UTF-8\r\n\r\n` +
    `${JSON.stringify(meta)}\r\n`;

  const dataPart =
    `--${boundary}\r\n` +
    `Content-Type: ${params.mimeType}\r\n` +
    `Content-Transfer-Encoding: base64\r\n\r\n` +
    `${params.contentBase64}\r\n` +
    `--${boundary}--`;

  const res = await fetch(`${DRIVE_UPLOAD}?uploadType=multipart`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': `multipart/related; boundary=${boundary}`,
    },
    body: metaPart + dataPart,
  } as any);

  if (!res.ok) throw new Error(`Drive upload failed: ${res.status} ${res.statusText} - ${await res.text()}`);
  return res.json();
}
