import type { IExecuteFunctions, INodeType, INodeTypeDescription } from 'n8n-workflow';
import { stripePost } from '../utils/stripe';

export class StripeCreatePaymentIntent implements INodeType {
  description: INodeTypeDescription = {
    displayName: 'Stripe - Create Payment Intent',
    name: 'stripeCreatePaymentIntent',
    group: ['transform'],
    version: 1,
    description: 'Cria um PaymentIntent no Stripe',
    defaults: { name: 'Stripe PaymentIntent' },
    inputs: ['main'],
    outputs: ['main'],
    properties: [
      { displayName: 'Amount (em cents)', name: 'amount', type: 'number', default: 100, required: true },
      { displayName: 'Currency (ex: usd, brl)', name: 'currency', type: 'string', default: 'usd', required: true },
      { displayName: 'Customer (opcional)', name: 'customer', type: 'string', default: '' },
      { displayName: 'Receipt Email (opcional)', name: 'receipt_email', type: 'string', default: '' },
      { displayName: 'Description (opcional)', name: 'description', type: 'string', default: '' },
      { displayName: 'Payment Method Types (JSON array)', name: 'payment_method_types', type: 'json', default: '["card"]' },
      { displayName: 'Extra Fields (raw form fields JSON)', name: 'extraFields', type: 'json', default: '{}' }
    ],
  };

  async execute(this: IExecuteFunctions) {
    const items = this.getInputData(); const out: any[] = [];
    for (let i = 0; i < items.length; i++) {
      const amount = this.getNodeParameter('amount', i) as number;
      const currency = this.getNodeParameter('currency', i) as string;
      const customer = this.getNodeParameter('customer', i) as string;
      const receipt_email = this.getNodeParameter('receipt_email', i) as string;
      const description = this.getNodeParameter('description', i) as string;
      const payment_method_types = this.getNodeParameter('payment_method_types', i) as any[];
      const extraFields = this.getNodeParameter('extraFields', i) as Record<string, any>;

      const body: Record<string, any> = {
        amount, currency,
        ...(customer ? { customer } : {}),
        ...(receipt_email ? { receipt_email } : {}),
        ...(description ? { description } : {}),
        ...(payment_method_types ? { 'payment_method_types[]': payment_method_types } : {}),
        ...(extraFields || {}),
      };

      const res = await stripePost('payment_intents', body);
      out.push({ json: { request: body, response: res } });
    }
    return this.prepareOutputData(out);
  }
}
