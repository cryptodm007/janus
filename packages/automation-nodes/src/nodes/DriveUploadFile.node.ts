import type { IExecuteFunctions, INodeType, INodeTypeDescription } from 'n8n-workflow';
import { driveUploadFile } from '../utils/googleDrive';

export class DriveUploadFile implements INodeType {
  description: INodeTypeDescription = {
    displayName: 'Google Drive - Upload File',
    name: 'driveUploadFile',
    group: ['transform'],
    version: 1,
    description: 'Faz upload de arquivo para o Google Drive (Service Account)',
    defaults: { name: 'Drive Upload File' },
    inputs: ['main'],
    outputs: ['main'],
    properties: [
      { displayName: 'File Name', name: 'name', type: 'string', default: 'file.txt', required: true },
      { displayName: 'MIME Type', name: 'mimeType', type: 'string', default: 'text/plain' },
      { displayName: 'Content (base64)', name: 'contentBase64', type: 'string', default: '', required: true },
      { displayName: 'Parent Folder ID (opcional)', name: 'parentId', type: 'string', default: '' },
    ],
  };

  async execute(this: IExecuteFunctions) {
    const items = this.getInputData(); const out: any[] = [];
    for (let i = 0; i < items.length; i++) {
      const name = this.getNodeParameter('name', i) as string;
      const mimeType = this.getNodeParameter('mimeType', i) as string;
      const contentBase64 = this.getNodeParameter('contentBase64', i) as string;
      const parentId = (this.getNodeParameter('parentId', i) as string) || undefined;
      const res = await driveUploadFile({ name, mimeType, contentBase64, parentId });
      out.push({ json: { request: { name, mimeType, parentId }, response: res } });
    }
    return this.prepareOutputData(out);
  }
}
