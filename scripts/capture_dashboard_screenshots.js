import { spawn } from 'child_process';
import fs from 'fs';
import path from 'path';
import os from 'os';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const EDGE_PATH = "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe";
const EDGE_USER_DATA = path.join(os.tmpdir(), "exam_edge_screenshot_profile");
const FRONTEND_URL = "http://localhost:3000";

const outputDir = path.join(__dirname, "..", "deliverables", "chuyenhvt_screenshots");
if (!fs.existsSync(outputDir)) {
  fs.mkdirSync(outputDir, { recursive: true });
}
if (!fs.existsSync(EDGE_USER_DATA)) {
  fs.mkdirSync(EDGE_USER_DATA, { recursive: true });
}

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function sendCdp(ws, method, params = {}) {
  const id = Math.floor(Math.random() * 1000000);
  return new Promise((resolve, reject) => {
    const handleMsg = (event) => {
      const data = JSON.parse(event.data);
      if (data.id === id) {
        ws.removeEventListener('message', handleMsg);
        if (data.error) reject(data.error);
        else resolve(data.result);
      }
    };
    ws.addEventListener('message', handleMsg);
    ws.send(JSON.stringify({ id, method, params }));
  });
}

async function main() {
  console.log("[1] Spawning Edge for screenshot capture...");
  const edgeArgs = [
    '--headless=new',
    '--remote-debugging-port=9225',
    '--disable-gpu',
    '--no-first-run',
    '--no-default-browser-check',
    `--user-data-dir=${EDGE_USER_DATA}`,
    FRONTEND_URL
  ];

  const edgeProc = spawn(EDGE_PATH, edgeArgs, { stdio: 'ignore' });

  try {
    console.log("[2] Connecting to CDP port 9225...");
    let pageTarget = null;
    for (let i = 0; i < 20; i++) {
      await sleep(500);
      try {
        const res = await fetch("http://127.0.0.1:9225/json");
        if (res.ok) {
          const targets = await res.json();
          pageTarget = targets.find(t => t.type === 'page' && t.url.includes("localhost:3000"));
          if (pageTarget && pageTarget.webSocketDebuggerUrl) break;
        }
      } catch (e) {}
    }

    if (!pageTarget) {
      throw new Error("Could not find localhost:3000 target on CDP");
    }

    console.log(`[3] Connecting WebSocket to: ${pageTarget.webSocketDebuggerUrl}`);
    const ws = new WebSocket(pageTarget.webSocketDebuggerUrl);
    await new Promise((resolve, reject) => {
      ws.onopen = resolve;
      ws.onerror = reject;
    });

    await sendCdp(ws, "Page.enable");
    await sendCdp(ws, "DOM.enable");
    await sendCdp(ws, "Page.navigate", { url: FRONTEND_URL });

    // Wait 4 seconds for full React hydration & asset rendering
    await sleep(4000);

    const viewports = [
      { name: "dashboard_1648px.png", width: 1648, height: 924 },
      { name: "dashboard_1440px.png", width: 1440, height: 900 },
      { name: "dashboard_1280px.png", width: 1280, height: 800 },
      { name: "dashboard_1024px.png", width: 1024, height: 768 }
    ];

    for (const vp of viewports) {
      console.log(`[4] Capturing ${vp.name} (${vp.width}x${vp.height})...`);
      await sendCdp(ws, "Emulation.setDeviceMetricsOverride", {
        width: vp.width,
        height: vp.height,
        deviceScaleFactor: 1,
        mobile: false
      });
      await sleep(600);

      const shot = await sendCdp(ws, "Page.captureScreenshot", { format: "png" });
      const filePath = path.join(outputDir, vp.name);
      fs.writeFileSync(filePath, Buffer.from(shot.data, "base64"));
      console.log(`[OK] Saved: ${filePath} (${fs.statSync(filePath).size} bytes)`);
    }

    ws.close();
  } catch (err) {
    console.error("[ERROR]", err);
  } finally {
    edgeProc.kill();
  }
}

main();
