import type { IExecuteFunctions, INodeType, INodeTypeDescription } from 'n8n-workflow';
import { airtableCreate, airtableUpdate } from '../utils/airtable';

// Upsert simples: se tiver "id" no registro -> PATCH, senão -> POST.
// Para estratégias por "campo único", você pode primeiro buscar (AirtableFind) e então mapear IDs, antes de rodar o Upsert.

export class AirtableUpsert implements INodeType {
  description: INodeTypeDescription = {
    displayName: 'Airtable Upsert',
    name: 'airtableUpsert',
    group: ['transform'],
    version: 1,
    description: 'Cria e/ou atualiza registros em uma tabela do Airtable',
    defaults: { name: 'Airtable Upsert' },
    inputs: ['main'],
    outputs: ['main'],
    properties: [
      { displayName: 'Table Name', name: 'table', type: 'string', default: '', required: true },
      { displayName: 'Records (JSON array: {id?, fields:{...}})', name: 'records', type: 'json', default: '[]' },
      { displayName: 'Typecast (coagir tipos em updates)', name: 'typecast', type: 'boolean', default: false },
    ],
  };

  async execute(this: IExecuteFunctions) {
    const items = this.getInputData();
    const out: any[] = [];
    for (let i = 0; i < items.length; i++) {
      const table = this.getNodeParameter('table', i) as string;
      const records = this.getNodeParameter('records', i) as any[];
      const typecast = this.getNodeParameter('typecast', i) as boolean;

      const toUpdate = (records || []).filter((r) => r && r.id);
      const toCreate = (records || []).filter((r) => r && !r.id);

      let createRes: any = null;
      let updateRes: any = null;

      if (toCreate.length) createRes = await airtableCreate(table, toCreate);
      if (toUpdate.length) updateRes = await airtableUpdate(table, toUpdate, typecast);

      out.push({ json: { created: createRes, updated: updateRes } });
    }
    return this.prepareOutputData(out);
  }
}
