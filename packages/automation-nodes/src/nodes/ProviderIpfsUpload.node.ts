import type { IExecuteFunctions, INodeType, INodeTypeDescription } from 'n8n-workflow';
import { providerRequest } from '../utils/web3Provider';

const DEFAULT_IPFS_PATH = 'v3/ipfs/file';

export class ProviderIpfsUpload implements INodeType {
  description: INodeTypeDescription = {
    displayName: 'Web3 API - IPFS Upload',
    name: 'providerIpfsUpload',
    group: ['transform'],
    version: 1,
    description: 'Faz upload de arquivo/conteúdo para IPFS via API externa',
    defaults: { name: 'IPFS Upload' },
    inputs: ['main'],
    outputs: ['main'],
    properties: [
      { displayName: 'Endpoint Path', name: 'endpointPath', type: 'string', default: DEFAULT_IPFS_PATH },
      { displayName: 'Filename', name: 'filename', type: 'string', default: 'file.txt' },
      { displayName: 'Content (base64)', name: 'contentBase64', type: 'string', default: '' },
      { displayName: 'Raw Extra Body (JSON, opcional)', name: 'extraBody', type: 'json', default: '{}' },
    ],
  };

  async execute(this: IExecuteFunctions) {
    const items = this.getInputData();
    const out: any[] = [];

    for (let i = 0; i < items.length; i++) {
      const endpointPath = this.getNodeParameter('endpointPath', i) as string;
      const filename = this.getNodeParameter('filename', i) as string;
      const contentBase64 = this.getNodeParameter('contentBase64', i) as string;
      const extraBody = this.getNodeParameter('extraBody', i) as any;

      if (!contentBase64) throw new Error('contentBase64 is required');

      const body: any = { filename, content: contentBase64, ...extraBody };
      const res = await providerRequest<any>(endpointPath, 'POST', body);
      out.push({ json: { request: { filename }, response: res } });
    }
    return this.prepareOutputData(out);
  }
}
