import type { IExecuteFunctions, INodeType, INodeTypeDescription } from 'n8n-workflow';
import { twilioSendMessage } from '../utils/twilio';

export class TwilioMessageOut implements INodeType {
  description: INodeTypeDescription = {
    displayName: 'Twilio Message (SMS/WhatsApp)',
    name: 'twilioMessageOut',
    group: ['transform'],
    version: 1,
    description: 'Envia mensagem via Twilio (SMS/WhatsApp)',
    defaults: { name: 'Twilio Message' },
    inputs: ['main'], outputs: ['main'],
    properties: [
      { displayName: 'To (ex: +5511999999999 ou whatsapp:+5511999999999)', name: 'to', type: 'string', default: '', required: true },
      { displayName: 'From (sender number)', name: 'from', type: 'string', default: '' },
      { displayName: 'Messaging Service SID (alternativo ao From)', name: 'messagingServiceSid', type: 'string', default: '' },
      { displayName: 'Body', name: 'body', type: 'string', default: '' },
      { displayName: 'Media URL (opcional)', name: 'mediaUrl', type: 'string', default: '' },
    ],
  };

  async execute(this: IExecuteFunctions) {
    const items = this.getInputData(); const out: any[] = [];
    for (let i = 0; i < items.length; i++) {
      const to = this.getNodeParameter('to', i) as string;
      const from = this.getNodeParameter('from', i) as string;
      const messagingServiceSid = this.getNodeParameter('messagingServiceSid', i) as string;
      const body = this.getNodeParameter('body', i) as string;
      const mediaUrl = this.getNodeParameter('mediaUrl', i) as string;
      const res = await twilioSendMessage(from, to, body, messagingServiceSid || undefined, mediaUrl || undefined);
      out.push({ json: { to, body, response: res } });
    }
    return this.prepareOutputData(out);
  }
}
