import { once } from 'node:events';
import { createServer } from 'node:http';
import { test, expect } from '@playwright/test';
import { installPreviewNetworkGuard } from './helpers.mjs';

test('COMM-V1 network guard refuses non-preview requests', async ({context, page}) => {
  const unexpected = [];
  const outside = createServer((request, response) => {
    unexpected.push(request.url);
    response.end('unexpected request');
  });
  let outsideOrigin;
  const preview = createServer((request, response) => {
    if (request.method === 'GET' && request.url === '/') {
      response.setHeader('Content-Type', 'text/html');
      response.end('<!doctype html><title>Synthetic isolation fixture</title><link rel="icon" href="data:,">');
    } else if (request.method === 'GET' && request.url === '/redirect') {
      response.writeHead(302, {Location: outsideOrigin + '/redirected'});
      response.end();
    } else {
      unexpected.push(request.method + ' ' + request.url);
      response.writeHead(404).end();
    }
  });
  preview.on('upgrade', (request, socket) => {
    unexpected.push(request.url);
    socket.destroy();
  });
  outside.listen(0, '127.0.0.1');
  preview.listen(0, '127.0.0.1');
  try {
    await Promise.all([once(outside, 'listening'), once(preview, 'listening')]);
    outsideOrigin = 'http://127.0.0.1:' + outside.address().port;
    const origin = 'http://127.0.0.1:' + preview.address().port;
    await installPreviewNetworkGuard(context, origin);
    const response = await page.goto(origin);
    expect(response?.ok()).toBe(true);

    for (const [url, method] of [
      [outsideOrigin + '/fetch', 'GET'],
      [origin + '/mutation', 'POST'],
      [origin + '/redirect', 'GET'],
    ]) {
      const failed = context.waitForEvent('requestfailed', {predicate: request => request.url() === url});
      const result = await page.evaluate(async ({url, method}) => {
        return fetch(url, {method}).then(() => 'allowed', () => 'refused');
      }, {url, method});
      expect(result).toBe('refused');
      expect((await failed).failure()?.errorText).toContain('ERR_BLOCKED_BY_CLIENT');
    }

    const popupURL = outsideOrigin + '/popup';
    const popupFailure = context.waitForEvent('requestfailed', {predicate: request => request.url() === popupURL});
    await page.evaluate(url => { window.open(url); }, popupURL);
    expect((await popupFailure).failure()?.errorText).toContain('ERR_BLOCKED_BY_CLIENT');

    const serviceWorkers = await page.evaluate(async () => {
      await navigator.serviceWorker.register('/worker.js').catch(() => {});
      return (await navigator.serviceWorker.getRegistrations()).length;
    });
    expect(serviceWorkers).toBe(0);

    const socket = await page.evaluate(() => new Promise(resolve => {
      const ws = new WebSocket('ws://' + location.host + '/socket');
      ws.onopen = () => resolve('allowed');
      ws.onclose = () => resolve('refused');
    }));
    expect(socket).toBe('refused');
    expect(unexpected).toEqual([]);
  } finally {
    outside.close();
    preview.close();
  }
});
