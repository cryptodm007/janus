const API = process.env.GITHUB_API_BASE || 'https://api.github.com';
const TOKEN = process.env.GITHUB_TOKEN || '';

export async function githubCreateIssue(owner: string, repo: string, title: string, body?: string, labels?: string[]) {
  if (!TOKEN) throw new Error('Missing GITHUB_TOKEN');
  if (!owner || !repo || !title) throw new Error('owner, repo and title are required');

  const res = await fetch(`${API}/repos/${owner}/${repo}/issues`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${TOKEN}`,
      'Accept': 'application/vnd.github+json',
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ title, body, labels }),
  } as any);

  if (!res.ok) throw new Error(`GitHub create issue failed: ${res.status} ${res.statusText} - ${await res.text()}`);
  return res.json();
}
