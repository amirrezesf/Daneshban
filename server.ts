import express from 'express';
import http from 'http';
import { spawn, ChildProcess } from 'child_process';
import path from 'path';

const app = express();
const PORT = 3000;
const DJANGO_PORT = 8001;
const BASE_DIR = process.cwd();

// Launch Django development server in background
let djangoProcess: ChildProcess | null = null;

function startDjango() {
  const pythonPath = path.join(BASE_DIR, '.venv', 'bin', 'python');
  djangoProcess = spawn(pythonPath, ['manage.py', 'runserver', `127.0.0.1:${DJANGO_PORT}`], {
    cwd: BASE_DIR,
    stdio: 'inherit',
    env: { ...process.env, PYTHONUNBUFFERED: '1' }
  });

  djangoProcess.on('exit', (code, signal) => {
    console.log(`Django process exited with code ${code} and signal ${signal}`);
  });
}

startDjango();

// Reverse proxy middleware to forward all requests to Django
app.use((req, res) => {
  const targetUrl = new URL(req.url, `http://127.0.0.1:${DJANGO_PORT}`);
  const options: http.RequestOptions = {
    hostname: '127.0.0.1',
    port: DJANGO_PORT,
    path: targetUrl.pathname + targetUrl.search,
    method: req.method,
    headers: {
      ...req.headers,
      host: req.headers.host || `localhost:${PORT}`,
      'x-forwarded-host': req.headers.host || `localhost:${PORT}`,
      'x-forwarded-proto': (req.headers['x-forwarded-proto'] as string) || 'https',
      'x-forwarded-for': req.ip || '127.0.0.1',
    },
  };

  const proxyReq = http.request(options, (proxyRes) => {
    res.writeHead(proxyRes.statusCode || 200, proxyRes.headers);
    proxyRes.pipe(res);
  });

  proxyReq.on('error', (err) => {
    // During startup, Django might take 1-2 seconds to boot
    res.status(502).send(`
      <!DOCTYPE html>
      <html lang="fa" dir="rtl">
      <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>در حال راه‌اندازی سرور جنگو...</title>
        <style>
          body { font-family: Tahoma, sans-serif; text-align: center; padding: 50px 20px; background: #f8fafc; color: #1e293b; direction: rtl; }
          .card { max-width: 500px; margin: 0 auto; background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
          .spinner { width: 36px; height: 36px; border: 4px solid #e2e8f0; border-top-color: #2563eb; border-radius: 50%; animation: spin 1s linear infinite; margin: 20px auto; }
          @keyframes spin { 100% { transform: rotate(360deg); } }
        </style>
      </head>
      <body>
        <div class="card">
          <h2>در حال آماده‌سازی سامانه دانشگاهی...</h2>
          <div class="spinner"></div>
          <p>سرور جنگو در حال بارگذاری است. صفحه پس از چند ثانیه خودکار تازه‌سازی می‌شود.</p>
          <script>setTimeout(function() { window.location.reload(); }, 2000);</script>
        </div>
      </body>
      </html>
    `);
  });

  req.pipe(proxyReq);
});

const server = app.listen(PORT, '0.0.0.0', () => {
  console.log(`Gateway reverse proxy listening on http://0.0.0.0:${PORT} -> Django ${DJANGO_PORT}`);
});

process.on('SIGTERM', () => {
  if (djangoProcess) djangoProcess.kill();
  server.close();
});

process.on('SIGINT', () => {
  if (djangoProcess) djangoProcess.kill();
  server.close();
});
