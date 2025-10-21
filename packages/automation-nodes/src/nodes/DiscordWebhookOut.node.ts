import type { IExecuteFunctions, INodeType, INodeTypeDescription } from 'n8n-workflow';
import { discordWebhookSend } from '../utils/discord';

export class DiscordWebhookOut implements INodeType {
  description: INodeTypeDescription = {
    displayName: 'Discord Webhook (Out)',
    name: 'discordWebhookOut',
    group: ['transform'],
    version: 1,
    description: 'Envia conteúdo para um Discord Webhook URL',
    defaults: { name: 'Discord Webhook (Out)' },
    inputs: ['main'],
    outputs: ['main'],
    properties: [
      { displayName: 'Webhook URL', name: 'url', type: 'string', default: '', required: true },
      { displayName: 'Payload (JSON)', name: 'payload', type: 'json', default: '{"content":"Hello from Janus!"}' },
    ],
  };

  async execute(this: IExecuteFunctions) {
    const items = this.getInputData();
    const out: any[] = [];
    for (let i = 0; i < items.length; i++) {
      const url = this.getNodeParameter('url', i) as string;
      const payload = this.getNodeParameter('payload', i) as any;
      const res = await discordWebhookSend(url, payload);
      out.push({ json: { request: { url, payload }, response: res } });
    }
    return this.prepareOutputData(out);
  }
}
