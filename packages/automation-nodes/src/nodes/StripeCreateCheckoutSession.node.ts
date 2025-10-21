import type { IExecuteFunctions, INodeType, INodeTypeDescription } from 'n8n-workflow';
import { stripePost } from '../utils/stripe';

export class StripeCreateCheckoutSession implements INodeType {
  description: INodeTypeDescription = {
    displayName: 'Stripe - Create Checkout Session',
    name: 'stripeCreateCheckoutSession',
    group: ['transform'],
    version: 1,
    description: 'Cria uma sessão de checkout no Stripe',
    defaults: { name: 'Stripe Checkout Session' },
    inputs: ['main'],
    outputs: ['main'],
    properties: [
      { displayName: 'Mode', name: 'mode', type: 'options',
        options: [{ name: 'payment', value: 'payment' }, { name: 'subscription', value: 'subscription' }], default: 'payment' },
      { displayName: 'Success URL', name: 'success_url', type: 'string', default: '', required: true },
      { displayName: 'Cancel URL', name: 'cancel_url', type: 'string', default: '', required: true },
      { displayName: 'Line Items (raw form fields JSON)', name: 'lineItemsRaw', type: 'json', default: '{}',
        description: 'Ex.: {"line_items[0][price]":"price_123","line_items[0][quantity]":"1"}' },
      { displayName: 'Extra Fields (raw form fields JSON)', name: 'extraFields', type: 'json', default: '{}',
        description: 'Ex.: {"customer_email":"x@y.com"}' }
    ],
  };

  async execute(this: IExecuteFunctions) {
    const items = this.getInputData(); const out: any[] = [];

    for (let i = 0; i < items.length; i++) {
      const mode = this.getNodeParameter('mode', i) as string;
      const success_url = this.getNodeParameter('success_url', i) as string;
      const cancel_url = this.getNodeParameter('cancel_url', i) as string;
      const lineItemsRaw = this.getNodeParameter('lineItemsRaw', i) as Record<string, any>;
      const extraFields = this.getNodeParameter('extraFields', i) as Record<string, any>;

      const body: Record<string, any> = { mode, success_url, cancel_url, ...(lineItemsRaw || {}), ...(extraFields || {}) };
      const res = await stripePost('checkout/sessions', body);
      out.push({ json: { request: body, response: res } });
    }
    return this.prepareOutputData(out);
  }
}
