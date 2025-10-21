import type { IExecuteFunctions, INodeType, INodeTypeDescription } from 'n8n-workflow';
import { airtableList } from '../utils/airtable';

export class AirtableFind implements INodeType {
  description: INodeTypeDescription = {
    displayName: 'Airtable Find',
    name: 'airtableFind',
    group: ['transform'],
    version: 1,
    description: 'Busca registros em uma tabela do Airtable',
    defaults: { name: 'Airtable Find' },
    inputs: ['main'],
    outputs: ['main'],
    properties: [
      { displayName: 'Table Name', name: 'table', type: 'string', default: '', required: true },
      { displayName: 'Filter by Formula (opcional)', name: 'filterByFormula', type: 'string', default: '' },
      { displayName: 'Max Records', name: 'maxRecords', type: 'number', default: 100 },
      { displayName: 'Page Size', name: 'pageSize', type: 'number', default: 100 },
      { displayName: 'View (opcional)', name: 'view', type: 'string', default: '' },
    ],
  };

  async execute(this: IExecuteFunctions) {
    const items = this.getInputData();
    const out: any[] = [];
    for (let i = 0; i < items.length; i++) {
      const table = this.getNodeParameter('table', i) as string;
      const filterByFormula = this.getNodeParameter('filterByFormula', i) as string;
      const maxRecords = this.getNodeParameter('maxRecords', i) as number;
      const pageSize = this.getNodeParameter('pageSize', i) as number;
      const view = this.getNodeParameter('view', i) as string;

      const res = await airtableList(table, {
        filterByFormula: filterByFormula || undefined,
        maxRecords: maxRecords || undefined,
        pageSize: pageSize || undefined,
        view: view || undefined,
      });

      out.push({ json: res });
    }
    return this.prepareOutputData(out);
  }
}
