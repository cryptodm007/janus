import type { IExecuteFunctions, INodeType, INodeTypeDescription } from 'n8n-workflow';
import { slackWebhookSend } from '../utils/slack';

export class SlackWebhookOut implements INodeType {
  description: INodeTypeDescription = {
    displayName: 'Slack Webhook (Out)',
    name: 'slackWebhookOut',
    group: ['transform'],
    version: 1,
    description: 'Envia payload para um Slack Incoming Webhook URL',
    defaults: { name: 'Slack Webhook (Out)' },
    inputs: ['main'], outputs: ['main'],
    properties: [
      { displayName: 'Webhook URL', name: 'url', type: 'string', default: '', required: true },
      { displayName: 'Payload (JSON)', name: 'payload', type: 'json', default: '{"text":"Hello from Janus!"}' },
    ],
  };

  async execute(this: IExecuteFunctions) {
    const items = this.getInputData(); const out: any[] = [];
    for (let i = 0; i < items.length; i++) {
      const url = this.getNodeParameter('url', i) as string;
      const payload = this.getNodeParameter('payload', i) as any;
      const res = await slackWebhookSend(url, payload);
      out.push({ json: { request: { url, payload }, response: res } });
    }
    return this.prepareOutputData(out);
  }
}
