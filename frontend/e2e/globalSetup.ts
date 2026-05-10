/**
 * Start backend services (mock LLM + mock agent + AutoGLM-GUI) before E2E tests.
 *
 * Uses child_process to manage the Python launcher script.  The PID is written
 * to a file so globalTeardown can kill it.
 */
import { spawn } from 'child_process';
import path from 'path';
import fs from 'fs';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

async function globalSetup() {
  const projectRoot = path.resolve(__dirname, '..', '..');
  const urlsPath = path.resolve(__dirname, '.service_urls.json');
  const pidPath = path.resolve(__dirname, '.services_pid');

  console.log('[globalSetup] Starting E2E services...');

  // Stop services from the previous E2E run, if that run did not clean up.
  try {
    const previousPid = Number(fs.readFileSync(pidPath, 'utf-8').trim());
    if (Number.isFinite(previousPid)) {
      process.kill(-previousPid, 'SIGTERM');
      await new Promise(r => setTimeout(r, 1000));
      try {
        process.kill(-previousPid, 'SIGKILL');
      } catch {
        /* previous process group is already gone */
      }
    }
  } catch {
    /* PID file may not exist */
  }

  // Cleanup old files
  try {
    fs.unlinkSync(urlsPath);
  } catch {
    /* file may not exist */
  }
  try {
    fs.unlinkSync(pidPath);
  } catch {
    /* file may not exist */
  }

  // Wait for ports to be fully released by the OS
  await new Promise(r => setTimeout(r, 3000));

  console.log('[globalSetup] Project root:', projectRoot);

  // Start services with retry on port-in-use
  let proc: ReturnType<typeof spawn> | null = null;
  for (let attempt = 0; attempt < 3; attempt++) {
    proc = spawn(
      'uv',
      ['run', 'python', 'scripts/start_e2e_services.py', '--output', urlsPath],
      {
        cwd: projectRoot,
        stdio: 'inherit',
        detached: true,
      }
    );

    // Wait for the backend health endpoint
    const deadline = Date.now() + 30000;
    let started = false;
    while (Date.now() < deadline) {
      try {
        const resp = await fetch('http://127.0.0.1:8000/api/health');
        if (resp.status === 200) {
          const urls = JSON.parse(fs.readFileSync(urlsPath, 'utf-8'));
          console.log('[globalSetup] Services ready, URLs:', urls);
          started = true;
          break;
        }
      } catch {
        // Not ready — but check if the process exited with error
        if (proc && proc.exitCode !== null) {
          // Process died — port likely in use, retry
          console.log(
            `[globalSetup] Attempt ${attempt + 1}: process exited, retrying...`
          );
          break;
        }
      }
      await new Promise(r => setTimeout(r, 500));
    }
    if (started && proc?.pid) {
      fs.writeFileSync(pidPath, String(proc.pid));
      return;
    }
    // Kill the failed process and wait before retry
    if (proc) {
      proc.kill('SIGTERM');
      await new Promise(r => setTimeout(r, 2000));
    }
  }

  throw new Error('E2E services failed to start after 3 attempts');
}

export default globalSetup;
