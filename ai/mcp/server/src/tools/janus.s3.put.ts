import { S3PutInput } from "../schema.js";
import { s3Put } from "../../../../packages/connectors/aws/s3.js";

export async function s3PutObject(input: unknown) {
  const p = S3PutInput.parse(input);
  return s3Put({
    bucket: p.bucket,
    key: p.key,
    body: p.content,
    contentType: p.contentType
  });
}
