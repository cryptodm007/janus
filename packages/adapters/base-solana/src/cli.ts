import { spawn } from 'child_process';

export interface RunResult {
  ok: boolean;
  stdout: string;
  stderr: string;
  code: number | null;
}

export function runCommand(commandLine: string, args: string[] = [], opts: { cwd?: string; env?: NodeJS.ProcessEnv } = {}): Promise<RunResult> {
  return new Promise((resolve) => {
    const [cmd, ...cmdArgs] = commandLine.split(' ');
    const child = spawn(cmd, [...cmdArgs, ...args], {
      cwd: opts.cwd ?? process.cwd(),
      env: { ...process.env, ...(opts.env || {}) },
      shell: process.platform === 'win32',
    });

    let stdout = '';
    let stderr = '';

    child.stdout.setEncoding('utf8');
    child.stdout.on('data', (d) => (stdout += d));
    child.stderr.setEncoding('utf8');
    child.stderr.on('data', (d) => (stderr += d));

    child.on('close', (code) => {
      const ok = code == 0;
      resolve({ ok, stdout, stderr, code });
    });
  });
}

export function parseMaybeJson(s: string): any | null {
  try {
    return JSON.parse(s);
  } catch {
    return null;
  }
}
