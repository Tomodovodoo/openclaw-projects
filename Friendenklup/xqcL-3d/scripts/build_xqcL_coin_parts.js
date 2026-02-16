import fs from 'node:fs';
import path from 'node:path';
import { PNG } from 'pngjs';

const ROOT = path.resolve(path.dirname(new URL(import.meta.url).pathname), '..');
const SOURCE_PNG = path.join(ROOT, 'source', 'xqcL.png');
const EMOJI_URL = 'https://cdn.discordapp.com/emojis/898264218439131226.png?size=512&quality=lossless';

const OUT_DIR = path.join(ROOT, 'output', 'print_parts');
const OUT_BASE = path.join(OUT_DIR, 'xqcL_coin_base_60mm.stl');
const OUT_PALETTE = path.join(OUT_DIR, 'palette.json');

function ensureDir(p) { fs.mkdirSync(p, { recursive: true }); }
async function downloadIfMissing(url, outPath) {
  if (fs.existsSync(outPath)) return;
  const res = await fetch(url);
  if (!res.ok) throw new Error(`download failed: ${res.status} ${res.statusText}`);
  const ab = await res.arrayBuffer();
  fs.writeFileSync(outPath, Buffer.from(ab));
}

function clamp(v, lo, hi) { return Math.max(lo, Math.min(hi, v)); }

function sampleRGBA_bilinear(img, u, v) {
  const { width: w, height: h, data } = img;
  const x = clamp(u, 0, 1) * (w - 1);
  const y = clamp(v, 0, 1) * (h - 1);

  const x0 = Math.floor(x), y0 = Math.floor(y);
  const x1 = Math.min(x0 + 1, w - 1);
  const y1 = Math.min(y0 + 1, h - 1);
  const tx = x - x0;
  const ty = y - y0;

  function px(ix, iy) {
    const i = (iy * w + ix) * 4;
    return [data[i] / 255, data[i + 1] / 255, data[i + 2] / 255, data[i + 3] / 255];
  }
  const c00 = px(x0, y0);
  const c10 = px(x1, y0);
  const c01 = px(x0, y1);
  const c11 = px(x1, y1);

  const out = [0, 0, 0, 0];
  for (let k = 0; k < 4; k++) {
    const a = c00[k] * (1 - tx) + c10[k] * tx;
    const b = c01[k] * (1 - tx) + c11[k] * tx;
    out[k] = a * (1 - ty) + b * ty;
  }
  return out;
}

function luminance(r, g, b) {
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}

function rgbToHex([r, g, b]) {
  const R = clamp(Math.round(r * 255), 0, 255).toString(16).padStart(2, '0');
  const G = clamp(Math.round(g * 255), 0, 255).toString(16).padStart(2, '0');
  const B = clamp(Math.round(b * 255), 0, 255).toString(16).padStart(2, '0');
  return `#${R}${G}${B}`;
}

function kmeansDeterministic(points, k, iters = 10) {
  // points: Array<[r,g,b]> in 0..1
  if (points.length === 0) throw new Error('no points');

  // deterministic init: sort by luminance and pick evenly spaced.
  const sorted = [...points].sort((a, b) => luminance(...a) - luminance(...b));
  const centers = [];
  for (let i = 0; i < k; i++) {
    const idx = Math.floor((i + 0.5) * (sorted.length / k));
    centers.push([...sorted[clamp(idx, 0, sorted.length - 1)]]);
  }

  const assign = new Uint16Array(points.length);

  for (let iter = 0; iter < iters; iter++) {
    // assign
    for (let i = 0; i < points.length; i++) {
      const p = points[i];
      let best = 0;
      let bestD = Infinity;
      for (let c = 0; c < centers.length; c++) {
        const cc = centers[c];
        const dr = p[0] - cc[0];
        const dg = p[1] - cc[1];
        const db = p[2] - cc[2];
        const d = dr * dr + dg * dg + db * db;
        if (d < bestD) { bestD = d; best = c; }
      }
      assign[i] = best;
    }

    // recompute
    const sum = Array.from({ length: k }, () => [0, 0, 0, 0]);
    for (let i = 0; i < points.length; i++) {
      const c = assign[i];
      const p = points[i];
      sum[c][0] += p[0];
      sum[c][1] += p[1];
      sum[c][2] += p[2];
      sum[c][3] += 1;
    }
    for (let c = 0; c < k; c++) {
      if (sum[c][3] > 0) {
        centers[c][0] = sum[c][0] / sum[c][3];
        centers[c][1] = sum[c][1] / sum[c][3];
        centers[c][2] = sum[c][2] / sum[c][3];
      }
    }
  }

  return centers;
}

function nearestCenterIndex(p, centers) {
  let best = 0;
  let bestD = Infinity;
  for (let c = 0; c < centers.length; c++) {
    const cc = centers[c];
    const dr = p[0] - cc[0];
    const dg = p[1] - cc[1];
    const db = p[2] - cc[2];
    const d = dr * dr + dg * dg + db * db;
    if (d < bestD) { bestD = d; best = c; }
  }
  return best;
}

function buildBaseCoinSTL({
  diameterMM = 60,
  baseThicknessMM = 3.0,
  rimWidthMM = 2.2,
  rimHeightMM = 0.8,
  segments = 256,
}) {
  const R = diameterMM / 2;
  const innerR = Math.max(0, R - rimWidthMM);
  const rimZ = baseThicknessMM + rimHeightMM;

  // Proper “coin + raised rim”: flat disc top at baseThickness, flat rim top at rimZ,
  // with a vertical step wall at innerR.
  const V = [];
  const tris = [];
  const topDisc = new Array(segments);
  const topRimInner = new Array(segments);
  const topRimOuter = new Array(segments);
  const botOuter = new Array(segments);

  function pushV(x, y, z) { V.push([x, y, z]); return V.length - 1; }
  function addTri(a, b, c) { tris.push([a, b, c]); }

  const vTopCenter = pushV(0, 0, baseThicknessMM);
  const vBotCenter = pushV(0, 0, 0);

  for (let s = 0; s < segments; s++) {
    const th = (s / segments) * Math.PI * 2;
    const cx = Math.cos(th);
    const cy = Math.sin(th);

    topDisc[s] = pushV(innerR * cx, innerR * cy, baseThicknessMM);
    topRimInner[s] = pushV(innerR * cx, innerR * cy, rimZ);
    topRimOuter[s] = pushV(R * cx, R * cy, rimZ);
    botOuter[s] = pushV(R * cx, R * cy, 0);
  }

  // Top disc fan
  for (let s = 0; s < segments; s++) {
    const s1 = (s + 1) % segments;
    addTri(vTopCenter, topDisc[s], topDisc[s1]);
  }

  // Top rim band (flat)
  for (let s = 0; s < segments; s++) {
    const s1 = (s + 1) % segments;
    const a = topRimInner[s];
    const b = topRimInner[s1];
    const c = topRimOuter[s1];
    const d = topRimOuter[s];
    addTri(a, d, c);
    addTri(a, c, b);
  }

  // Bottom full disc fan (to outer)
  for (let s = 0; s < segments; s++) {
    const s1 = (s + 1) % segments;
    addTri(vBotCenter, botOuter[s1], botOuter[s]);
  }

  // Outer wall
  for (let s = 0; s < segments; s++) {
    const s1 = (s + 1) % segments;
    const a = botOuter[s];
    const b = botOuter[s1];
    const c = topRimOuter[s1];
    const d = topRimOuter[s];
    addTri(a, b, c);
    addTri(a, c, d);
  }

  // Inner step wall at innerR
  for (let s = 0; s < segments; s++) {
    const s1 = (s + 1) % segments;
    const a = topDisc[s];
    const b = topDisc[s1];
    const c = topRimInner[s1];
    const d = topRimInner[s];
    addTri(a, b, c);
    addTri(a, c, d);
  }

  return { V, tris };
}

function writeBinarySTL({ V, tris }, outPath, headerText = 'xqcL STL') {
  const triCount = tris.length;
  const out = Buffer.alloc(84 + triCount * 50);
  out.write(headerText.slice(0, 80), 0, 'ascii');
  out.writeUInt32LE(triCount, 80);

  let o = 84;
  const normal = (a, b, c) => {
    const A = V[a], B = V[b], C = V[c];
    const ux = B[0] - A[0], uy = B[1] - A[1], uz = B[2] - A[2];
    const vx = C[0] - A[0], vy = C[1] - A[1], vz = C[2] - A[2];
    let nx = uy * vz - uz * vy;
    let ny = uz * vx - ux * vz;
    let nz = ux * vy - uy * vx;
    const len = Math.hypot(nx, ny, nz) || 1;
    return [nx / len, ny / len, nz / len];
  };

  for (const [a, b, c] of tris) {
    const [nx, ny, nz] = normal(a, b, c);
    out.writeFloatLE(nx, o + 0);
    out.writeFloatLE(ny, o + 4);
    out.writeFloatLE(nz, o + 8);
    const A = V[a], B = V[b], C = V[c];
    out.writeFloatLE(A[0], o + 12);
    out.writeFloatLE(A[1], o + 16);
    out.writeFloatLE(A[2], o + 20);
    out.writeFloatLE(B[0], o + 24);
    out.writeFloatLE(B[1], o + 28);
    out.writeFloatLE(B[2], o + 32);
    out.writeFloatLE(C[0], o + 36);
    out.writeFloatLE(C[1], o + 40);
    out.writeFloatLE(C[2], o + 44);
    out.writeUInt16LE(0, o + 48);
    o += 50;
  }

  fs.writeFileSync(outPath, out);
}

function breakDiagonalContacts(mask, W, H) {
  // Remove edge-touch-only diagonal adjacencies that create non-manifold “kissing” geometry.
  // Deterministic rule: for pattern
  // 1 0
  // 0 1  -> remove bottom-right
  // 0 1
  // 1 0  -> remove bottom-left
  const idx = (x, y) => y * W + x;
  for (let y = 0; y < H - 1; y++) {
    for (let x = 0; x < W - 1; x++) {
      const a = mask[idx(x, y)];
      const b = mask[idx(x + 1, y)];
      const c = mask[idx(x, y + 1)];
      const d = mask[idx(x + 1, y + 1)];
      if (a && !b && !c && d) mask[idx(x + 1, y + 1)] = 0;
      if (!a && b && c && !d) mask[idx(x, y + 1)] = 0;
    }
  }
}

function removeIsolated(mask, W, H) {
  const idx = (x, y) => y * W + x;
  const out = new Uint8Array(mask);
  for (let y = 0; y < H; y++) {
    for (let x = 0; x < W; x++) {
      const i = idx(x, y);
      if (!mask[i]) continue;
      const n =
        (x > 0 ? mask[idx(x - 1, y)] : 0) +
        (x < W - 1 ? mask[idx(x + 1, y)] : 0) +
        (y > 0 ? mask[idx(x, y - 1)] : 0) +
        (y < H - 1 ? mask[idx(x, y + 1)] : 0);
      if (n === 0) out[i] = 0;
    }
  }
  mask.set(out);
}

function voxelPartSTL({
  mask, // Uint8Array W*H values: 1 means included
  heightsTop, // Float32Array W*H zTop in mm
  W, H,
  px, // mm per pixel
  originX, originY, // lower-left coord
  zBottom, // base plane
  outPath,
  header,
}) {
  const V = [];
  const tris = [];

  // Map grid corner vertex positions; we build per-face without shared verts (simpler, still reasonable sizes).
  // But we will only emit boundary faces to reduce size.

  const idx = (x, y) => y * W + x;

  function addQuad(ax, ay, az, bx, by, bz, cx, cy, cz, dx, dy, dz) {
    // two tris (a,b,c) (a,c,d)
    const iA = V.push([ax, ay, az]) - 1;
    const iB = V.push([bx, by, bz]) - 1;
    const iC = V.push([cx, cy, cz]) - 1;
    const iD = V.push([dx, dy, dz]) - 1;
    tris.push([iA, iB, iC], [iA, iC, iD]);
  }

  // emit prisms for each included cell
  for (let y = 0; y < H; y++) {
    for (let x = 0; x < W; x++) {
      const i = idx(x, y);
      if (!mask[i]) continue;

      const x0 = originX + x * px;
      const x1 = originX + (x + 1) * px;
      const y0 = originY + y * px;
      const y1 = originY + (y + 1) * px;
      const z0 = zBottom;
      const z1 = heightsTop[i];

      // Top face
      addQuad(x0, y0, z1, x1, y0, z1, x1, y1, z1, x0, y1, z1);
      // Bottom face (reverse winding by swapping)
      addQuad(x0, y0, z0, x0, y1, z0, x1, y1, z0, x1, y0, z0);

      // Sides only on boundaries
      // -x
      if (x === 0 || !mask[idx(x - 1, y)]) {
        addQuad(x0, y0, z0, x0, y0, z1, x0, y1, z1, x0, y1, z0);
      }
      // +x
      if (x === W - 1 || !mask[idx(x + 1, y)]) {
        addQuad(x1, y0, z0, x1, y1, z0, x1, y1, z1, x1, y0, z1);
      }
      // -y
      if (y === 0 || !mask[idx(x, y - 1)]) {
        addQuad(x0, y0, z0, x1, y0, z0, x1, y0, z1, x0, y0, z1);
      }
      // +y
      if (y === H - 1 || !mask[idx(x, y + 1)]) {
        addQuad(x0, y1, z0, x0, y1, z1, x1, y1, z1, x1, y1, z0);
      }
    }
  }

  writeBinarySTL({ V, tris }, outPath, header);
}

async function main() {
  ensureDir(path.join(ROOT, 'source'));
  ensureDir(path.join(ROOT, 'output'));
  ensureDir(OUT_DIR);

  await downloadIfMissing(EMOJI_URL, SOURCE_PNG);
  const img = PNG.sync.read(fs.readFileSync(SOURCE_PNG));

  // Coin parameters
  const diameterMM = 60;
  const baseThicknessMM = 3.0;
  const reliefHeightMM = 1.6;
  const minReliefMM = 0.05;
  const rimWidthMM = 2.2;
  const rimHeightMM = 0.8;
  const innerR = (diameterMM / 2) - rimWidthMM;
  const emojiScale = 0.82;
  const reliefGamma = 1.15;

  // Grid resolution for segmentation parts
  const W = 160;
  const H = 160;
  const innerDiameter = innerR * 2;
  const px = innerDiameter / W;
  const originX = -innerR;
  const originY = -innerR;

  const alphaCut = 0.08;
  const circleCut = 0.995; // keep within circle

  // Gather sample points for k-means
  const points = [];
  for (let y = 0; y < H; y += 2) {
    for (let x = 0; x < W; x += 2) {
      const cx = originX + (x + 0.5) * px;
      const cy = originY + (y + 0.5) * px;
      const rr = Math.hypot(cx, cy);
      if (rr > innerR * circleCut) continue;
      const u = 0.5 + (cx / (2 * innerR * emojiScale));
      const v = 0.5 - (cy / (2 * innerR * emojiScale));
      const [r, g, b, a] = sampleRGBA_bilinear(img, u, v);
      if (a < alphaCut) continue;
      points.push([r, g, b]);
    }
  }

  const K = 4;
  const centers = kmeansDeterministic(points, K, 10);

  // Save palette
  const palette = centers
    .map((c) => ({ hex: rgbToHex(c), rgb01: c }))
    .sort((a, b) => luminance(...a.rgb01) - luminance(...b.rgb01));

  fs.writeFileSync(OUT_PALETTE, JSON.stringify({ K, palette }, null, 2) + '\n');

  // Build per-pixel classification (we output constant-height color parts for watertightness)
  const classIdx = new Uint8Array(W * H);
  const inside = new Uint8Array(W * H);

  for (let y = 0; y < H; y++) {
    for (let x = 0; x < W; x++) {
      const cx = originX + (x + 0.5) * px;
      const cy = originY + (y + 0.5) * px;
      const rr = Math.hypot(cx, cy);
      if (rr > innerR * circleCut) {
        inside[y * W + x] = 0;
        classIdx[y * W + x] = 255;
        continue;
      }
      const u = 0.5 + (cx / (2 * innerR * emojiScale));
      const v = 0.5 - (cy / (2 * innerR * emojiScale));
      const [r, g, b, a] = sampleRGBA_bilinear(img, u, v);
      if (a < alphaCut) {
        inside[y * W + x] = 0;
        classIdx[y * W + x] = 255;
        continue;
      }
      inside[y * W + x] = 1;
      const ci = nearestCenterIndex([r, g, b], centers);
      classIdx[y * W + x] = ci;
    }
  }

  // Base coin (single piece)
  const baseMesh = buildBaseCoinSTL({ diameterMM, baseThicknessMM, rimWidthMM, rimHeightMM, segments: 256 });
  writeBinarySTL(baseMesh, OUT_BASE, 'xqcL coin base 60mm');

  // Color parts: one STL per class
  for (let c = 0; c < K; c++) {
    const mask = new Uint8Array(W * H);
    for (let i = 0; i < mask.length; i++) {
      mask[i] = inside[i] && classIdx[i] === c ? 1 : 0;
    }
    // Clean up mask to avoid non-manifold “diagonal kissing” edges + tiny specks.
    removeIsolated(mask, W, H);
    breakDiagonalContacts(mask, W, H);

    const out = path.join(OUT_DIR, `xqcL_coin_color_${c}.stl`);
    const overlayHeightMM = 0.65;
    const heightsTopConst = new Float32Array(W * H);
    for (let i = 0; i < heightsTopConst.length; i++) heightsTopConst[i] = baseThicknessMM + overlayHeightMM;

    voxelPartSTL({
      mask,
      heightsTop: heightsTopConst,
      W,
      H,
      px,
      originX,
      originY,
      zBottom: baseThicknessMM,
      outPath: out,
      header: `xqcL coin color part ${c}`,
    });
  }

  console.log(`Wrote base: ${OUT_BASE}`);
  console.log(`Wrote palette: ${OUT_PALETTE}`);
  console.log(`Wrote ${K} color part STLs to ${OUT_DIR}`);
}

main().catch((e) => { console.error(e); process.exit(1); });
