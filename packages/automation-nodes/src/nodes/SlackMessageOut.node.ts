import type { IExecuteFunctions, INodeType, INodeTypeDescription } from 'n8n-workflow';
import { slackPostMessage } from '../utils/slack';

export class SlackMessageOut implements INodeType {
  description: INodeTypeDescription = {
    displayName: 'Slack Message (Bot)',
    name: 'slackMessageOut',
    group: ['transform'],
    version: 1,
    description: 'Envia mensagem a um canal Slack usando Bot Token',
    defaults: { name: 'Slack Message (Bot)' },
    inputs: ['main'], outputs: ['main'],
    properties: [
      { displayName: 'Channel (ex: #geral ou C123...)', name: 'channel', type: 'string', default: '', required: true },
      { displayName: 'Text', name: 'text', type: 'string', default: '' },
      { displayName: 'Blocks (JSON array)', name: 'blocks', type: 'json', default: '[]' },
      { displayName: 'Attachments (JSON array)', name: 'attachments', type: 'json', default: '[]' },
    ],
  };

  async execute(this: IExecuteFunctions) {
    const items = this.getInputData(); const out: any[] = [];
    for (let i = 0; i < items.length; i++) {
      const channel = this.getNodeParameter('channel', i) as string;
      const text = this.getNodeParameter('text', i) as string;
      const blocks = this.getNodeParameter('blocks', i) as any[];
      const attachments = this.getNodeParameter('attachments', i) as any[];
      const res = await slackPostMessage(channel, text, blocks, attachments);
      out.push({ json: { channel, text, response: res } });
    }
    return this.prepareOutputData(out);
  }
}
