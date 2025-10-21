import type { IExecuteFunctions, INodeType, INodeTypeDescription } from 'n8n-workflow';
import { discordSendMessage } from '../utils/discord';

export class DiscordMessageOut implements INodeType {
  description: INodeTypeDescription = {
    displayName: 'Discord Message (Bot)',
    name: 'discordMessageOut',
    group: ['transform'],
    version: 1,
    description: 'Envia mensagem a um canal do Discord usando Bot Token',
    defaults: { name: 'Discord Message (Bot)' },
    inputs: ['main'],
    outputs: ['main'],
    properties: [
      { displayName: 'Channel ID', name: 'channelId', type: 'string', default: '', required: true },
      { displayName: 'Content', name: 'content', type: 'string', default: '' },
      { displayName: 'Embeds (JSON array)', name: 'embeds', type: 'json', default: '[]' },
      { displayName: 'Components (JSON array)', name: 'components', type: 'json', default: '[]' },
      { displayName: 'TTS', name: 'tts', type: 'boolean', default: false },
    ],
  };

  async execute(this: IExecuteFunctions) {
    const items = this.getInputData();
    const out: any[] = [];
    for (let i = 0; i < items.length; i++) {
      const channelId = this.getNodeParameter('channelId', i) as string;
      const content = this.getNodeParameter('content', i) as string;
      const embeds = this.getNodeParameter('embeds', i) as any[];
      const components = this.getNodeParameter('components', i) as any[];
      const tts = this.getNodeParameter('tts', i) as boolean;

      const res = await discordSendMessage({ channelId, content, embeds, components, tts });
      out.push({ json: { request: { channelId, content }, response: res } });
    }
    return this.prepareOutputData(out);
  }
}
