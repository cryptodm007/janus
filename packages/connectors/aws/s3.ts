import { S3Client, PutObjectCommand, GetObjectCommand } from "@aws-sdk/client-s3";
import { Readable } from "stream";

type PutReq = { bucket: string; key: string; body: string | Uint8Array; contentType?: string };
type GetReq = { bucket: string; key: string };

function s3() {
  return new S3Client({
    region: process.env.AWS_REGION || "us-east-1",
    credentials: { accessKeyId: process.env.AWS_ACCESS_KEY_ID || "", secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY || "" }
  });
}

export async function s3Put(req: PutReq) {
  const cli = s3();
  const out = await cli.send(new PutObjectCommand({ Bucket: req.bucket, Key: req.key, Body: req.body, ContentType: req.contentType }));
  return { etag: out.ETag };
}

export async function s3Get(req: GetReq) {
  const cli = s3();
  const out = await cli.send(new GetObjectCommand({ Bucket: req.bucket, Key: req.key }));
  const stream = out.Body as Readable;
  const chunks: Buffer[] = [];
  for await (const c of stream) chunks.push(c as Buffer);
  return Buffer.concat(chunks).toString("utf8");
}
