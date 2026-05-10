import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

async function globalTeardown() {
  const pidPath = path.resolve(__dirname, '.services_pid');
  const urlsPath = path.resolve(__dirname, '.service_urls.json');

  // Kill by saved PID (using process group to get children too)
  try {
    const pid = fs.readFileSync(pidPath, 'utf-8').trim();
    console.log(`[globalTeardown] Killing process group ${pid}`);
    try {
      process.kill(-Number(pid), 'SIGTERM');
    } catch {
      /* PID file may not exist or process already dead */
    }
    await new Promise(r => setTimeout(r, 1000));
    try {
      process.kill(-Number(pid), 'SIGKILL');
    } catch {
      /* PID file may not exist or process already dead */
    }
  } catch {
    // PID file may not exist
  }

  // Cleanup ONLY the processes we started (by PID file).
  // We do NOT kill processes by port or name — that would affect
  // unrelated services the user may be running.

  // Cleanup files
  try {
    fs.unlinkSync(pidPath);
  } catch {
    /* PID file may not exist or process already dead */
  }
  try {
    fs.unlinkSync(urlsPath);
  } catch {
    /* PID file may not exist or process already dead */
  }

  console.log('[globalTeardown] Cleanup complete');
}

export default globalTeardown;
