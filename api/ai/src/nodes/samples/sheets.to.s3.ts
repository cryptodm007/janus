import { googleSheets } from "../../../../packages/connectors/index.js";
import { awsS3 } from "../../../../packages/connectors/index.js";

export async function sheetsToS3(params: any) {
  const { spreadsheetId, range, bucket, key } = params;
  if (!spreadsheetId || !range || !bucket || !key) throw new Error("spreadsheetId/range/bucket/key required");
  const rows = await googleSheets.sheetsRead({
    spreadsheetId,
    range,
    credentials: {
      clientEmail: process.env.GOOGLE_CLIENT_EMAIL || "",
      privateKey: (process.env.GOOGLE_PRIVATE_KEY || "").replace(/\\n/g, "\n")
    }
  });
  const content = JSON.stringify(rows.values || rows, null, 2);
  const put = await awsS3.s3Put({ bucket, key, body: content, contentType: "application/json" });
  return { ok: true, etag: put.etag, size: content.length };
}
