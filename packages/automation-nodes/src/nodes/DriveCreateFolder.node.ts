import type { IExecuteFunctions, INodeType, INodeTypeDescription } from 'n8n-workflow';
import { driveCreateFolder } from '../utils/googleDrive';

export class DriveCreateFolder implements INodeType {
  description: INodeTypeDescription = {
    displayName: 'Google Drive - Create Folder',
    name: 'driveCreateFolder',
    group: ['transform'],
    version: 1,
    description: 'Cria uma pasta no Google Drive (Service Account)',
    defaults: { name: 'Drive Create Folder' },
    inputs: ['main'],
    outputs: ['main'],
    properties: [
      { displayName: 'Folder Name', name: 'name', type: 'string', default: '', required: true },
      { displayName: 'Parent Folder ID (opcional)', name: 'parentId', type: 'string', default: '' },
    ],
  };

  async execute(this: IExecuteFunctions) {
    const items = this.getInputData(); const out: any[] = [];
    for (let i = 0; i < items.length; i++) {
      const name = this.getNodeParameter('name', i) as string;
      const parentId = (this.getNodeParameter('parentId', i) as string) || undefined;
      const res = await driveCreateFolder(name, parentId);
      out.push({ json: { request: { name, parentId }, response: res } });
    }
    return this.prepareOutputData(out);
  }
}
