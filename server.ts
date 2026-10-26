import express from 'express';
import http from 'http';
import { spawn, ChildProcess } from 'child_process';
import path from 'path';
import fs from 'fs';

const app = express();
const PORT = 3000;
const DJANGO_PORT = 8001;
const BASE_DIR = process.cwd();

// Find python executable: preference for .venv/bin/python then python3
function getPythonPath(): string {
  const venvPython = path.join(BASE_DIR, '.venv', 'bin', 'python');
  if (fs.existsSync(venvPython)) {
    return venvPython;
  }
  return 'python3';
}

let djangoProcess: ChildProcess | null = null;
let isShuttingDown = false;
let restartAttempts = 0;

function startDjango() {
  if (isShuttingDown) return;

  const pythonExecutable = getPythonPath();
  console.log(`[Proxy] Starting Django with ${pythonExecutable} on port ${DJANGO_PORT}...`);

  djangoProcess = spawn(pythonExecutable, ['manage.py', 'runserver', `127.0.0.1:${DJANGO_PORT}`], {
    cwd: BASE_DIR,
    stdio: 'inherit',
    env: { ...process.env, PYTHONUNBUFFERED: '1' }
  });

  djangoProcess.on('error', (err) => {
    console.error(`[Proxy] Failed to spawn Django:`, err);
  });

  djangoProcess.on('exit', (code, signal) => {
    console.log(`[Proxy] Django process exited with code ${code} and signal ${signal}`);
    djangoProcess = null;
    if (!isShuttingDown) {
      restartAttempts++;
      const delay = Math.min(2000 * Math.min(restartAttempts, 5), 10000);
      console.log(`[Proxy] Will attempt to restart Django in ${delay}ms...`);
      setTimeout(startDjango, delay);
    }
  });
}

startDjango();

// Reverse proxy middleware to forward all requests to Django
app.use((req, res) => {
  const targetUrl = new URL(req.url, `http://127.0.0.1:${DJANGO_PORT}`);
  
  const incomingHost = (req.headers['x-forwarded-host'] as string) || req.headers.host || `localhost:${PORT}`;
  const incomingProto = (req.headers['x-forwarded-proto'] as string) || 'https';
  
  // Normalize origin header: if null or missing in sandboxed iframe, provide standard origin
  let originHeader = req.headers.origin;
  if (!originHeader || originHeader === 'null') {
    originHeader = `${incomingProto}://${incomingHost}`;
  }

  const options: http.RequestOptions = {
    hostname: '127.0.0.1',
    port: DJANGO_PORT,
    path: targetUrl.pathname + targetUrl.search,
    method: req.method,
    headers: {
      ...req.headers,
      host: incomingHost,
      origin: originHeader,
      'x-forwarded-host': incomingHost,
      'x-forwarded-proto': incomingProto,
      'x-forwarded-for': req.ip || '127.0.0.1',
    },
  };

  const proxyReq = http.request(options, (proxyRes) => {
    const headers = { ...proxyRes.headers };
    
    // Rewrite redirects to localhost:8001 or 127.0.0.1:8001 to relative path
    if (headers.location && typeof headers.location === 'string') {
      headers.location = headers.location
        .replace(/^https?:\/\/127\.0\.0\.1:8001/i, '')
        .replace(/^https?:\/\/localhost:8001/i, '');
      if (!headers.location.startsWith('/') && !headers.location.startsWith('http')) {
        headers.location = '/' + headers.location;
      }
    }

    // Allow embedding in AI Studio preview iframe
    delete headers['x-frame-options'];
    delete headers['cross-origin-opener-policy'];

    // Ensure session and CSRF cookies work in cross-origin preview iframes
    if (headers['set-cookie']) {
      const cookies = Array.isArray(headers['set-cookie'])
        ? headers['set-cookie']
        : [headers['set-cookie']];
      headers['set-cookie'] = cookies.map((cookieStr: string) => {
        let updated = cookieStr;
        if (!/SameSite=/i.test(updated)) {
          updated += '; SameSite=None';
        } else {
          updated = updated.replace(/SameSite=(Lax|Strict)/i, 'SameSite=None');
        }
        if (!/Secure/i.test(updated)) {
          updated += '; Secure';
        }
        return updated;
      });
    }

    res.writeHead(proxyRes.statusCode || 200, headers);
    proxyRes.pipe(res);
  });

  proxyReq.on('error', (_err) => {
    if (!res.headersSent) {
      res.status(502).send(`
        <!DOCTYPE html>
        <html lang="fa" dir="rtl">
        <head>
          <meta charset="utf-8">
          <meta name="viewport" content="width=device-width, initial-scale=1">
          <title>در حال راه‌اندازی سرور جنگو...</title>
          <style>
            body { font-family: Tahoma, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; text-align: center; padding: 50px 20px; background: #f8fafc; color: #1e293b; direction: rtl; }
            .card { max-width: 500px; margin: 0 auto; background: white; padding: 32px 24px; border-radius: 16px; box-shadow: 0 10px 25px -5px rgba(0,0,0,0.05), 0 8px 10px -6px rgba(0,0,0,0.01); border: 1px solid #e2e8f0; }
            .spinner { width: 40px; height: 40px; border: 4px solid #e2e8f0; border-top-color: #2563eb; border-radius: 50%; animation: spin 0.8s linear infinite; margin: 24px auto; }
            h2 { font-size: 1.25rem; font-weight: 700; margin-bottom: 0.5rem; color: #0f172a; }
            p { font-size: 0.95rem; color: #64748b; line-height: 1.6; }
            @keyframes spin { 100% { transform: rotate(360deg); } }
          </style>
        </head>
        <body>
          <div class="card">
            <h2>در حال راه‌اندازی سامانه مدیریت منابع دانشگاهی...</h2>
            <div class="spinner"></div>
            <p>سرویس‌ها در حال آماده‌سازی و بررسی پایگاه داده هستند. صفحه پس از چند لحظه خودکار بارگذاری می‌شود.</p>
            <script>setTimeout(function() { window.location.reload(); }, 2000);</script>
          </div>
        </body>
        </html>
      `);
    }
  });

  req.pipe(proxyReq);
});

const server = app.listen(PORT, '0.0.0.0', () => {
  console.log(`[Proxy] Gateway reverse proxy listening on http://0.0.0.0:${PORT} -> Django ${DJANGO_PORT}`);
});

function cleanup() {
  isShuttingDown = true;
  if (djangoProcess) {
    try {
      djangoProcess.kill('SIGTERM');
    } catch (e) {
      // ignore
    }
  }
  server.close();
}

process.on('SIGTERM', cleanup);
process.on('SIGINT', cleanup);
