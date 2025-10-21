import type { IExecuteFunctions, INodeType, INodeTypeDescription } from 'n8n-workflow';
import { sheetsRead } from '../utils/googleSheets';

export class SheetsRead implements INodeType {
  description: INodeTypeDescription = {
    displayName: 'Google Sheets - Read',
    name: 'sheetsRead',
    group: ['transform'],
    version: 1,
    description: 'Leitura de valores em uma planilha (Service Account)',
    defaults: { name: 'Sheets Read' },
    inputs: ['main'],
    outputs: ['main'],
    properties: [
      { displayName: 'Spreadsheet ID', name: 'spreadsheetId', type: 'string', default: '', required: true },
      { displayName: 'Range (A1 notation)', name: 'rangeA1', type: 'string', default: 'Sheet1!A1:B100', required: true },
    ],
  };

  async execute(this: IExecuteFunctions) {
    const items = this.getInputData(); const out: any[] = [];
    for (let i = 0; i < items.length; i++) {
      const spreadsheetId = this.getNodeParameter('spreadsheetId', i) as string;
      const rangeA1 = this.getNodeParameter('rangeA1', i) as string;
      const res = await sheetsRead(spreadsheetId, rangeA1);
      out.push({ json: res });
    }
    return this.prepareOutputData(out);
  }
}
