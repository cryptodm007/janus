import type { IExecuteFunctions, INodeType, INodeTypeDescription } from 'n8n-workflow';
import { notionCreatePage } from '../utils/notion';

export class NotionCreatePage implements INodeType {
  description: INodeTypeDescription = {
    displayName: 'Notion - Create Page',
    name: 'notionCreatePage',
    group: ['transform'],
    version: 1,
    description: 'Cria uma página em um Database do Notion',
    defaults: { name: 'Notion Create Page' },
    inputs: ['main'], outputs: ['main'],
    properties: [
      { displayName: 'Database ID', name: 'databaseId', type: 'string', default: '', required: true },
      { displayName: 'Properties (JSON)', name: 'properties', type: 'json', default: '{}' },
      { displayName: 'Children Blocks (JSON array, opcional)', name: 'children', type: 'json', default: '[]' }
    ],
  };

  async execute(this: IExecuteFunctions) {
    const items = this.getInputData(); const out: any[] = [];
    for (let i = 0; i < items.length; i++) {
      const databaseId = this.getNodeParameter('databaseId', i) as string;
      const properties = this.getNodeParameter('properties', i) as any;
      const children = this.getNodeParameter('children', i) as any[];
      const res = await notionCreatePage(databaseId, properties, children?.length ? children : undefined);
      out.push({ json: { databaseId, response: res } });
    }
    return this.prepareOutputData(out);
  }
}
