// 등불지기 키우기 광고 카드뉴스 렌더러: cards.json → html/0N.html → 헤드리스 크롬 캡처 → 01.png…, preview.jpg, cover_preview.jpg, phone_check.jpg
// 사용: node src/render.mjs   (이 주제 폴더에서). 크롬: Playwright 캐시의 chrome-headless-shell. PIL이 없는 환경이라 HTML+CSS로 그린다.
import { spawn } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const SRC = path.join(ROOT, 'src'), HTML = path.join(SRC, 'html');
const CHROME = process.env.CHROME || '/Users/ansangwoo/Library/Caches/ms-playwright/chromium_headless_shell-1223/chrome-headless-shell-mac-x64/chrome-headless-shell';
const data = JSON.parse(fs.readFileSync(path.join(SRC, 'cards.json'), 'utf8'));
const W = 1080, H = 1350, SRC_W = 1125;
const esc = s => String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));

// 원본 화면(1125px 폭)의 crop [x, y, w, h]을 목표 폭 tw로 보여 주는 상자
function shot(img, crop, tw, cls = '') {
  const [x, y, w, h] = crop, k = tw / w, th = Math.round(h * k);
  return `<div class="shot ${cls}" style="width:${tw}px;height:${th}px;background-image:url('../../assets/game/${img}');background-size:${Math.round(SRC_W * k)}px auto;background-position:${-Math.round(x * k)}px ${-Math.round(y * k)}px"></div>`;
}
const titleHtml = c => `<h1>${c.title.map((t, i) => `<span${i === c.hl ? ' class="hl"' : ''}>${esc(t)}</span>`).join('<br>')}</h1>`;

const CSS = `
@font-face{font-family:BHS;src:url('../../assets/BlackHanSans-Regular.ttf')}
*{box-sizing:border-box;margin:0;padding:0}
html,body{width:${W}px;height:${H}px;overflow:hidden}
body{position:relative;font-family:'Apple SD Gothic Neo',sans-serif;color:#f4f2ff;
 background:radial-gradient(120% 70% at 50% 0%,#2a1f63 0%,#14123a 45%,#0a0b22 100%)}
body:before{content:'';position:absolute;inset:0;pointer-events:none;opacity:.55;
 background-image:radial-gradient(2px 2px at 12% 18%,#fff8 50%,transparent 51%),radial-gradient(2px 2px at 78% 9%,#fff6 50%,transparent 51%),
 radial-gradient(3px 3px at 88% 42%,#ffe9a8aa 50%,transparent 51%),radial-gradient(2px 2px at 30% 64%,#fff5 50%,transparent 51%),
 radial-gradient(2px 2px at 58% 82%,#fff6 50%,transparent 51%),radial-gradient(3px 3px at 6% 88%,#c9b8ff99 50%,transparent 51%)}
.frame{position:absolute;inset:22px;border:2px solid #8f74ff66;border-radius:30px;box-shadow:inset 0 0 40px #6c4cff22,0 0 24px #7b5cff33;pointer-events:none;z-index:5}
.top{position:absolute;left:64px;right:64px;top:54px;display:flex;align-items:center;gap:14px;z-index:6}
.ad{padding:5px 16px 4px;border-radius:999px;background:#0b0c22cc;border:2px solid #fff;color:#fff;font:700 26px 'Apple SD Gothic Neo';letter-spacing:.5px}
.kicker{color:#ffd36b;font:800 26px 'Apple SD Gothic Neo';letter-spacing:3px}
.page{margin-left:auto;color:#c9c2ffcc;font:700 26px 'Apple SD Gothic Neo';letter-spacing:2px}
.foot{position:absolute;left:64px;right:64px;bottom:46px;display:flex;justify-content:space-between;align-items:flex-end;gap:20px;z-index:6;color:#b9b3e0;font:500 24px 'Apple SD Gothic Neo'}
.foot b{color:#fff;font-weight:700}
h1{font-family:BHS;font-weight:400;font-size:88px;line-height:1.08;letter-spacing:-1px;color:#fff;text-shadow:0 4px 0 #0008}
h1 .hl{color:#c8ff3c}
.body{font-size:36px;line-height:1.48;color:#e6e2ff;font-weight:600;letter-spacing:-.5px;word-break:keep-all}
.note{font-size:26px;color:#b9b3e0;font-weight:500}
.shot{background-repeat:no-repeat;border-radius:26px;box-shadow:0 0 0 3px #a58cff,0 0 0 9px #7b5cff33,0 18px 40px #000a;image-rendering:auto}
.text{position:absolute;left:64px;right:64px;z-index:4}
/* cover */
.cover .hero{position:absolute;left:0;top:0;width:${W}px}
.cover .hero .shot{border-radius:0;box-shadow:none}
.cover .fade{position:absolute;left:0;right:0;top:640px;height:380px;background:linear-gradient(#0a0b2200,#0a0b22ee 70%,#0a0b22)}
.cover .text{bottom:150px}
.cover h1{font-size:100px}
.cover .sub{margin-top:22px;font-size:38px;color:#e6e2ff;font-weight:700;word-break:keep-all}
/* full-bleed bottom text */
.full .hero{position:absolute;left:0;top:0}
.full .hero .shot{border-radius:0;box-shadow:none}
.full .fade{position:absolute;left:0;right:0;top:620px;height:420px;background:linear-gradient(#0a0b2200,#0a0b22f2 65%,#0a0b22)}
.full .text{bottom:130px}
.full .body{margin-top:20px}
/* top text + image */
.stack .text{top:118px}
.stack .body{margin-top:18px}
.stack .imgwrap{position:absolute;left:0;right:0;display:flex;justify-content:center}
.stack .note{position:absolute;left:64px;right:64px;text-align:center;z-index:4}
/* cta */
.cta .ctabox{position:absolute;left:64px;right:64px;bottom:118px;padding:26px 30px;border-radius:24px;background:linear-gradient(135deg,#c8ff3c,#9df06a);color:#141233;text-align:center;box-shadow:0 10px 30px #c8ff3c33}
.cta .ctabox b{display:block;font-family:BHS;font-weight:400;font-size:54px;line-height:1.1}
.cta .ctabox span{display:block;margin-top:10px;font:800 30px 'Apple SD Gothic Neo';letter-spacing:-.3px}
`;

function cardHtml(c, i, n) {
  const top = `<div class="top"><span class="ad">광고</span><span class="kicker">${esc(c.kicker)}</span><span class="page">${String(i + 1).padStart(2, '0')} / ${String(n).padStart(2, '0')}</span></div>`;
  const foot = `<div class="foot"><b>${esc(data.account)}</b><span>${esc(data.credit)}</span></div>`;
  let main = '', cls = '';
  if (c.layout === 'cover') {
    cls = 'cover';
    main = `<div class="hero">${shot(c.img, c.crop, W)}</div><div class="fade"></div><div class="text">${titleHtml(c)}<p class="sub">${esc(c.sub)}</p></div>`;
  } else if (c.layout === 'fullBottom') {
    cls = 'full';
    main = `<div class="hero">${shot(c.img, c.crop, W)}</div><div class="fade"></div><div class="text">${titleHtml(c)}<p class="body">${esc(c.body)}</p></div>`;
  } else {
    cls = c.layout === 'cta' ? 'stack cta' : 'stack';
    const imgTop = c.imgTop || 468;
    main = `<div class="text">${titleHtml(c)}<p class="body">${esc(c.body)}</p></div><div class="imgwrap" style="top:${imgTop}px">${shot(c.img, c.crop, c.w)}</div>`
      + (c.note ? `<p class="note" style="top:${c.noteTop || 1236}px">${esc(c.note)}</p>` : '')
      + (c.cta ? `<div class="ctabox"><b>${esc(c.cta[0])}</b><span>${esc(c.cta[1])}</span></div>` : '');
  }
  return `<!doctype html><html lang="ko"><head><meta charset="utf-8"><style>${CSS}</style></head><body class="${cls}"><div class="frame"></div>${top}${main}${foot}</body></html>`;
}

// ── 크롬 ──
const sleep = ms => new Promise(r => setTimeout(r, ms));
async function withChrome(fn) {
  const prof = fs.mkdtempSync(path.join(process.env.TMPDIR || '/tmp', 'lk-ad-'));
  const port = 9500 + Math.floor(Math.random() * 300);
  const proc = spawn(CHROME, ['--headless', `--remote-debugging-port=${port}`, `--user-data-dir=${prof}`, '--no-first-run', '--hide-scrollbars', '--allow-file-access-from-files', 'about:blank'], { stdio: 'ignore' });
  let ws, id = 0; const pending = new Map();
  const send = (method, params = {}) => new Promise((res, rej) => { const i = ++id; pending.set(i, { res, rej }); ws.send(JSON.stringify({ id: i, method, params })); });
  try {
    let list; for (let k = 0; k < 60; k++) { try { list = await (await fetch(`http://127.0.0.1:${port}/json/list`)).json(); if (list.length) break; } catch { } await sleep(200); }
    ws = new WebSocket(list.find(t => t.type === 'page').webSocketDebuggerUrl);
    await new Promise(r => ws.addEventListener('open', r));
    ws.addEventListener('message', e => { const m = JSON.parse(e.data); if (m.id && pending.has(m.id)) { const p = pending.get(m.id); pending.delete(m.id); m.error ? p.rej(new Error(m.error.message)) : p.res(m.result); } });
    await send('Page.enable');
    return await fn(send);
  } finally { try { ws && ws.close(); } catch { } proc.kill(); }
}
async function capture(send, file, out, w, h, fmt = 'png') {
  await send('Emulation.setDeviceMetricsOverride', { width: w, height: h, deviceScaleFactor: 1, mobile: false });
  await send('Page.navigate', { url: 'file://' + file });
  await sleep(900);
  const r = await send('Page.captureScreenshot', { format: fmt === 'jpg' ? 'jpeg' : 'png', quality: fmt === 'jpg' ? 90 : undefined, clip: { x: 0, y: 0, width: w, height: h, scale: 1 } });
  fs.writeFileSync(out, Buffer.from(r.data, 'base64'));
}

fs.mkdirSync(HTML, { recursive: true });
const n = data.cards.length;
const files = data.cards.map((c, i) => { const f = path.join(HTML, `${String(i + 1).padStart(2, '0')}.html`); fs.writeFileSync(f, cardHtml(c, i, n)); return f; });
await withChrome(async send => {
  for (let i = 0; i < n; i++) { await capture(send, files[i], path.join(ROOT, `${String(i + 1).padStart(2, '0')}.png`), W, H); console.log('card', i + 1); }
  // 전체 미리보기(3×2), 표지 미리보기, 휴대폰 크기 확인(가로 380px)
  const grid = (cols, w, gap) => `<!doctype html><meta charset=utf-8><body style="margin:0;background:#11111a;display:grid;grid-template-columns:repeat(${cols},${w}px);gap:${gap}px;padding:${gap}px">${data.cards.map((c, i) => `<img src="../../${String(i + 1).padStart(2, '0')}.png" style="width:${w}px;display:block;border-radius:6px">`).join('')}</body>`;
  fs.writeFileSync(path.join(HTML, 'preview.html'), grid(3, 360, 12));
  const rows = Math.ceil(n / 3);
  await capture(send, path.join(HTML, 'preview.html'), path.join(ROOT, 'preview.jpg'), 3 * 360 + 4 * 12, rows * 450 + (rows + 1) * 12, 'jpg');
  fs.writeFileSync(path.join(HTML, 'cover.html'), `<!doctype html><meta charset=utf-8><body style="margin:0"><img src="../../01.png" style="width:540px;display:block">`);
  await capture(send, path.join(HTML, 'cover.html'), path.join(ROOT, 'cover_preview.jpg'), 540, 675, 'jpg');
  fs.writeFileSync(path.join(HTML, 'phone.html'), grid(3, 380, 10));
  await capture(send, path.join(HTML, 'phone.html'), path.join(ROOT, 'phone_check.jpg'), 3 * 380 + 4 * 10, rows * 475 + (rows + 1) * 10, 'jpg');
});
console.log('done');
