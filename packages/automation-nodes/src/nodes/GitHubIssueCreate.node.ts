import type { IExecuteFunctions, INodeType, INodeTypeDescription } from 'n8n-workflow';
import { githubCreateIssue } from '../utils/github';

export class GitHubIssueCreate implements INodeType {
  description: INodeTypeDescription = {
    displayName: 'GitHub - Create Issue',
    name: 'githubIssueCreate',
    group: ['transform'],
    version: 1,
    description: 'Cria uma issue em um repositório do GitHub',
    defaults: { name: 'GitHub Create Issue' },
    inputs: ['main'], outputs: ['main'],
    properties: [
      { displayName: 'Owner', name: 'owner', type: 'string', default: '', required: true },
      { displayName: 'Repo', name: 'repo', type: 'string', default: '', required: true },
      { displayName: 'Title', name: 'title', type: 'string', default: '', required: true },
      { displayName: 'Body (opcional)', name: 'body', type: 'string', default: '' },
      { displayName: 'Labels (JSON array)', name: 'labels', type: 'json', default: '[]' }
    ],
  };

  async execute(this: IExecuteFunctions) {
    const items = this.getInputData(); const out: any[] = [];
    for (let i = 0; i < items.length; i++) {
      const owner = this.getNodeParameter('owner', i) as string;
      const repo = this.getNodeParameter('repo', i) as string;
      const title = this.getNodeParameter('title', i) as string;
      const body = this.getNodeParameter('body', i) as string;
      const labels = this.getNodeParameter('labels', i) as any[];
      const res = await githubCreateIssue(owner, repo, title, body, labels);
      out.push({ json: { owner, repo, title, response: res } });
    }
    return this.prepareOutputData(out);
  }
}
