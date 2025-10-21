import type { INodeType, INodeTypeDescription, ITriggerFunctions } from 'n8n-workflow';
import { providerRequest, delay } from '../utils/web3Provider';

// Trigger genérico: faz polling num endpoint GET e emite itens novos.
// Ideal para eventos de transações, mints, logs etc. do seu provedor.

export class ProviderEventSource implements INodeType {
  description: INodeTypeDescription = {
    displayName: 'Web3 API - Event Source (Trigger)',
    name: 'providerEventSource',
    group: ['trigger'],
    version: 1,
    description: 'Dispara workflow a partir de eventos do provedor (polling)',
    defaults: { name: 'Event Source' },
    inputs: [],
    outputs: ['main'],
    properties: [
      { displayName: 'Endpoint Path (GET)', name: 'endpointPath', type: 'string', default: 'v3/events' },
      { displayName: 'Polling Interval (ms)', name: 'intervalMs', type: 'number', default: 5000 },
      { displayName: 'JSON Path for Items', name: 'jsonPath', type: 'string', default: 'data' },
      { displayName: 'State Key (id/timestamp)', name: 'stateKey', type: 'string', default: 'id' },
    ],
  };

  async trigger(this: ITriggerFunctions) {
    const endpointPath = this.getNodeParameter('endpointPath', 0) as string;
    const intervalMs = this.getNodeParameter('intervalMs', 0) as number;
    const jsonPath = (this.getNodeParameter('jsonPath', 0) as string) || '';
    const stateKey = (this.getNodeParameter('stateKey', 0) as string) || 'id';

    const seen = new Set<string>();
    let active = true;

    const loop = async () => {
      while (active) {
        try {
          const res = await providerRequest<any>(endpointPath, 'GET');
          let items = res;
          if (jsonPath && res && typeof res === 'object' && res[jsonPath] !== undefined) items = res[jsonPath];

          if (Array.isArray(items)) {
            const fresh = items.filter((it) => {
              const key = (it && (it[stateKey] ?? it['id'] ?? it['txHash'])) as string | undefined;
              if (!key) return true;
              if (seen.has(String(key))) return false;
              seen.add(String(key));
              return true;
            });
            if (fresh.length > 0) {
              this.emit([this.helpers.returnJsonArray(fresh.map((it) => ({ source: 'provider', item: it })))]);
            }
          } else if (items) {
            this.emit([this.helpers.returnJsonArray([{ source: 'provider', item: items }])]);
          }
        } catch (e: any) {
          this.emitError(e);
        }
        await delay(intervalMs);
      }
    };

    loop();

    async function closeFunction() { active = false; }
    return { closeFunction };
  }
}
