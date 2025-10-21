import type { IExecuteFunctions, INodeType, INodeTypeDescription } from 'n8n-workflow';
import { telegramSendMessage } from '../utils/telegram';

export class TelegramMessageOut implements INodeType {
  description: INodeTypeDescription = {
    displayName: 'Telegram Message (Bot)',
    name: 'telegramMessageOut',
    group: ['transform'],
    version: 1,
    description: 'Envia mensagem a um chat do Telegram usando Bot Token',
    defaults: { name: 'Telegram Message (Bot)' },
    inputs: ['main'], outputs: ['main'],
    properties: [
      { displayName: 'Chat ID', name: 'chatId', type: 'string', default: '', required: true },
      { displayName: 'Text', name: 'text', type: 'string', default: '' },
      { displayName: 'Parse Mode', name: 'parseMode', type: 'options',
        options: [{ name: 'None', value: '' }, { name: 'Markdown', value: 'Markdown' }, { name: 'HTML', value: 'HTML' }], default: '' },
      { displayName: 'Disable Link Preview', name: 'disableWebPagePreview', type: 'boolean', default: false },
    ],
  };

  async execute(this: IExecuteFunctions) {
    const items = this.getInputData(); const out: any[] = [];
    for (let i = 0; i < items.length; i++) {
      const chatId = this.getNodeParameter('chatId', i) as string;
      const text = this.getNodeParameter('text', i) as string;
      const parseMode = this.getNodeParameter('parseMode', i) as string;
      const disableWebPagePreview = this.getNodeParameter('disableWebPagePreview', i) as boolean;
      const res = await telegramSendMessage(chatId, text, parseMode || undefined, disableWebPagePreview);
      out.push({ json: { chatId, text, response: res } });
    }
    return this.prepareOutputData(out);
  }
}
