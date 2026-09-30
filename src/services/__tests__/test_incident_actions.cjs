/* Browser regressions for AUD-05. All API/media/WS traffic is intercepted.
 * Run against an isolated Vite server with VITE_DEMO_MODE=false.
 * Playwright may be supplied through NODE_PATH; no project dependency update needed.
 */
const assert = require('node:assert/strict');
const { chromium } = require('playwright');

const baseUrl = process.env.AUDIT_UI_URL || 'http://127.0.0.1:3107';
const fixture = {
  id: 'audit_fixture', source_id: 'cam1', track_id: 7, violation_type: 'PHONE',
  confidence: 0.95, level: 'red', status: 'pending',
  detected_at: '2026-09-30T10:00:00Z', created_at: '2026-09-30T10:00:00Z',
  video_path: '/evidence/audit_fixture.mp4', snapshot_path: '/evidence/audit_fixture_snap.jpg',
};
const config = { phone_confidence: 0.55, posture_alert_seconds: 1.25, suspicion_threshold: 0.5,
  pre_roll_seconds: 5, post_roll_seconds: 10, cooldown_seconds: 6 };

async function setup(browser) {
  const context = await browser.newContext({ viewport: { width: 1600, height: 1000 } });
  const page = await context.newPage();
  const state = { rows: [{ ...fixture }], deletes: 0, confirms: 0, purge: 0, failDelete: false,
    failPurge: false, partialPurge: false, failList: false, runtimeErrors: [] };
  page.on('pageerror', error => state.runtimeErrors.push(error.message));
  page.on('dialog', dialog => dialog.accept());
  await page.addInitScript(() => {
    class TestSocket {
      static OPEN = 1; static CONNECTING = 0; static CLOSED = 3;
      readyState = 0; bufferedAmount = 0;
      constructor() { setTimeout(() => { if (this.readyState !== 3) { this.readyState = 1; this.onopen?.({}); } }, 0); }
      send() {}
      close() { this.readyState = 3; this.onclose?.({ code: 1000 }); }
    }
    window.WebSocket = TestSocket;
    navigator.mediaDevices.enumerateDevices = async () => [];
    navigator.mediaDevices.getUserMedia = async () => { throw new Error('Hardware disabled for audit test'); };
  });
  await page.route('**/*', async route => {
    const url = new URL(route.request().url());
    if (url.origin === baseUrl) return route.continue();
    const path = url.pathname;
    const method = route.request().method();
    const json = (body, status = 200) => route.fulfill({ status, contentType: 'application/json', body: JSON.stringify(body) });
    if (path === '/api/incidents' && method === 'GET') {
      return state.failList ? json({ detail: 'offline fixture' }, 503) : json(state.rows);
    }
    if (path === '/api/incidents/videos/purge-all') {
      state.purge++;
      if (state.failPurge) return json({ detail: 'Purge fixture failed' }, 500);
      if (state.partialPurge) return json({ success: false, message: 'Còn tệp chờ dọn dẹp' });
      state.rows = [];
      return json({ success: true, deleted_files_count: 2 });
    }
    if (path === '/api/incidents/audit_fixture' && method === 'DELETE') {
      state.deletes++;
      if (state.failDelete) return json({ detail: 'Deletion fixture failed' }, 500);
      state.rows = [];
      return json({ success: true });
    }
    if (path.endsWith('/confirm')) {
      state.confirms++;
      state.rows[0] = { ...state.rows[0], ...route.request().postDataJSON() };
      return json(state.rows[0]);
    }
    if (path === '/api/settings/ai') return json(config);
    if (path === '/api/camera/mode') return json({ mode: 'SINGLE_CAMERA' });
    if (path === '/api/camera/sources') return json({ mode: 'SINGLE_CAMERA', cameras: [], total_online: 0, demo_read_only: false });
    if (path === '/api/status') return json({ status: 'ONLINE', device: 'test', fps_estimate: 0,
      timestamp: fixture.detected_at, active_models: {}, total_session_incidents: 1, database_connected: true });
    return route.abort(); // Never reach a real backend, camera, or external host.
  });
  await page.goto(baseUrl);
  await page.waitForLoadState('networkidle');
  await page.getByRole('button', { name: 'Xem clip', exact: true }).waitFor();
  return { page, context, state };
}

async function eventually(check) {
  for (let attempt = 0; attempt < 100; attempt++) {
    if (await check()) return;
    await new Promise(resolve => setTimeout(resolve, 50));
  }
  assert.fail('UI assertion timed out');
}

(async () => {
  const browser = await chromium.launch({ channel: process.env.AUDIT_BROWSER_CHANNEL || 'chrome', headless: true });
  let passed = 0;
  try {
    {
      const { page, context, state } = await setup(browser);
      // Inspect the rendered UI before choosing the action selectors.
      assert.ok((await page.locator('button[title]').allTextContents()).length > 0);
      state.failDelete = true;
      await page.getByTitle('Xóa video và dữ liệu vi phạm này khỏi hệ thống', { exact: true }).click();
      await page.getByRole('alert').waitFor();
      assert.equal(state.deletes, 1, 'One click must issue one DELETE');
      assert.equal(await page.getByRole('button', { name: 'Xem clip', exact: true }).count(), 1);
      assert.equal(await page.getByText('Đã xóa tệp video sự cố thành công', { exact: true }).count(), 0);
      state.failDelete = false;
      await page.getByTitle('Xóa video và dữ liệu vi phạm này khỏi hệ thống', { exact: true }).click();
      await eventually(async () => (await page.getByRole('button', { name: 'Xem clip', exact: true }).count()) === 0);
      await page.getByText('Đã xóa tệp video sự cố thành công', { exact: true }).waitFor();
      assert.equal(state.deletes, 2, 'Successful retry must not call DELETE twice');
      assert.deepEqual(state.runtimeErrors, []);
      await context.close(); passed++;
      console.log('PASS: failed deletion preserves incident; successful retry sends one request');
    }
    {
      const { page, context, state } = await setup(browser);
      await page.getByRole('button', { name: 'Xem clip', exact: true }).click();
      state.failDelete = true;
      await page.getByRole('button', { name: 'Xóa video sự cố', exact: true }).click();
      await eventually(() => state.deletes === 1);
      await page.getByText('Deletion fixture failed', { exact: true }).waitFor();
      assert.equal(await page.getByRole('button', { name: 'Xóa video sự cố', exact: true }).count(), 1);
      state.failDelete = false;
      await page.getByRole('button', { name: 'Xóa video sự cố', exact: true }).click();
      await eventually(async () => (await page.getByRole('button', { name: 'Xóa video sự cố', exact: true }).count()) === 0);
      await eventually(async () => (await page.getByRole('button', { name: 'Xem clip', exact: true }).count()) === 0);
      assert.equal(state.deletes, 2);
      assert.deepEqual(state.runtimeErrors, []);
      await context.close(); passed++;
      console.log('PASS: modal remains open on failure; last incident disappears after success');
    }
    {
      const { page, context, state } = await setup(browser);
      const purge = async () => {
        await page.getByTitle('Xóa toàn bộ video bằng chứng vi phạm', { exact: true }).click();
        await page.getByRole('button', { name: 'Xác nhận xóa', exact: true }).click();
      };
      state.failPurge = true;
      await purge();
      await page.getByRole('alert').filter({ hasText: 'Purge fixture failed' }).waitFor();
      assert.equal(await page.getByRole('button', { name: 'Xem clip', exact: true }).count(), 1);
      state.failPurge = false; state.partialPurge = true;
      await purge();
      await page.getByRole('alert').filter({ hasText: 'Còn tệp chờ dọn dẹp' }).waitFor();
      assert.equal(await page.getByRole('button', { name: 'Xem clip', exact: true }).count(), 1);
      state.partialPurge = false;
      await purge();
      await eventually(async () => (await page.getByRole('button', { name: 'Xem clip', exact: true }).count()) === 0);
      assert.equal(await page.getByTitle('Xóa toàn bộ video bằng chứng vi phạm', { exact: true }).count(), 1,
        'Cleanup retry must remain available with no incident rows');
      assert.equal(state.purge, 3);
      assert.deepEqual(state.runtimeErrors, []);
      await context.close(); passed++;
      console.log('PASS: purge errors and partial cleanup stay visible; retry remains available');
    }
    {
      const { page, context, state } = await setup(browser);
      await page.getByTitle('Xác nhận vi phạm', { exact: true }).click();
      await page.getByText('✓ Đã duyệt', { exact: true }).waitFor();
      assert.equal(state.confirms, 1, 'Confirmation callback must not send another PATCH');
      state.failList = true;
      await page.getByTitle('Làm mới danh sách sự cố', { exact: true }).click();
      await page.getByRole('alert').filter({ hasText: 'Không thể tải sự cố' }).waitFor();
      assert.equal(await page.getByRole('button', { name: 'Xem clip', exact: true }).count(), 1);
      state.failList = false; state.rows = [];
      await page.getByTitle('Làm mới danh sách sự cố', { exact: true }).click();
      await eventually(async () => (await page.getByRole('button', { name: 'Xem clip', exact: true }).count()) === 0);
      assert.equal(await page.getByRole('alert').count(), 0);
      assert.deepEqual(state.runtimeErrors, []);
      await context.close(); passed++;
      console.log('PASS: one confirmation request; offline feed preserves rows and empty response clears them');
    }
    console.log(`${passed} browser regression scenarios passed`);
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
