import type { IExecuteFunctions, INodeType, INodeTypeDescription } from 'n8n-workflow';
import { sheetsAppend } from '../utils/googleSheets';

export class SheetsAppend implements INodeType {
  description: INodeTypeDescription = {
    displayName: 'Google Sheets - Append',
    name: 'sheetsAppend',
    group: ['transform'],
    version: 1,
    description: 'Append de linhas em uma planilha (Service Account)',
    defaults: { name: 'Sheets Append' },
    inputs: ['main'],
    outputs: ['main'],
    properties: [
      { displayName: 'Spreadsheet ID', name: 'spreadsheetId', type: 'string', default: '', required: true },
      { displayName: 'Range (A1 notation, ex: Sheet1!A1)', name: 'rangeA1', type: 'string', default: 'Sheet1!A1', required: true },
      { displayName: 'Values (JSON array de arrays)', name: 'values', type: 'json', default: '[]' },
      { displayName: 'Value Input Option', name: 'valueInputOption', type: 'options',
        options: [{ name: 'RAW', value: 'RAW' }, { name: 'USER_ENTERED', value: 'USER_ENTERED' }], default: 'RAW' },
    ],
  };

  async execute(this: IExecuteFunctions) {
    const items = this.getInputData(); const out: any[] = [];
    for (let i = 0; i < items.length; i++) {
      const spreadsheetId = this.getNodeParameter('spreadsheetId', i) as string;
      const rangeA1 = this.getNodeParameter('rangeA1', i) as string;
      const values = this.getNodeParameter('values', i) as any[][];
      const valueInputOption = this.getNodeParameter('valueInputOption', i) as 'RAW' | 'USER_ENTERED';
      const res = await sheetsAppend(spreadsheetId, rangeA1, values, valueInputOption);
      out.push({ json: { request: { spreadsheetId, rangeA1 }, response: res } });
    }
    return this.prepareOutputData(out);
  }
}
