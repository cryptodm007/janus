import { S3Client, PutObjectCommand } from "@aws-sdk/client-s3";

type PutReq = { bucket: string; key: string; body: string | Uint8Array; contentType?: string };

export async function s3Put(req: PutReq) {
  const s3 = new S3Client({
    region: process.env.AWS_REGION || "us-east-1",
    credentials: {
      accessKeyId: process.env.AWS_ACCESS_KEY_ID || "",
      secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY || ""
    }
  });
  const out = await s3.send(new PutObjectCommand({
    Bucket: req.bucket,
    Key: req.key,
    Body: req.body,
    ContentType: req.contentType
  }));
  return { etag: out.ETag };
}
