import type { IExecuteFunctions, INodeType, INodeTypeDescription } from 'n8n-workflow';
import { s3PutObject } from '../utils/s3';

export class S3PutObject implements INodeType {
  description: INodeTypeDescription = {
    displayName: 'AWS S3 - Put Object',
    name: 's3PutObject',
    group: ['transform'],
    version: 1,
    description: 'Envia arquivo para S3 (SigV4) usando credenciais AWS',
    defaults: { name: 'S3 Put Object' },
    inputs: ['main'],
    outputs: ['main'],
    properties: [
      { displayName: 'Region', name: 'region', type: 'string', default: 'us-east-1', required: true },
      { displayName: 'Bucket', name: 'bucket', type: 'string', default: '', required: true },
      { displayName: 'Key (ex: folder/file.txt)', name: 'key', type: 'string', default: '', required: true },
      { displayName: 'Content-Type (opcional)', name: 'contentType', type: 'string', default: '' },
      { displayName: 'ACL (opcional, ex: public-read)', name: 'acl', type: 'string', default: '' },
      { displayName: 'Body (base64)', name: 'bodyBase64', type: 'string', default: '', required: true },
    ],
  };

  async execute(this: IExecuteFunctions) {
    const items = this.getInputData(); const out: any[] = [];
    for (let i = 0; i < items.length; i++) {
      const region = this.getNodeParameter('region', i) as string;
      const bucket = this.getNodeParameter('bucket', i) as string;
      const key = this.getNodeParameter('key', i) as string;
      const contentType = (this.getNodeParameter('contentType', i) as string) || undefined;
      const acl = (this.getNodeParameter('acl', i) as string) || undefined;
      const bodyBase64 = this.getNodeParameter('bodyBase64', i) as string;

      const res = await s3PutObject({ region, bucket, key, contentType, acl, bodyBase64 });
      out.push({ json: { request: { region, bucket, key, contentType, acl }, response: res } });
    }
    return this.prepareOutputData(out);
  }
}
