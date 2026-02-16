import fs from 'node:fs';
import path from 'node:path';
import { PNG } from 'pngjs';

const ROOT = path.resolve(path.dirname(new URL(import.meta.url).pathname), '..');
const SOURCE_PNG = path.join(ROOT, 'source', 'xqcL.png');
const OUT_STL = path.join(ROOT, 'output', 'xqcL_coin_60mm.stl');
const OUT_OBJ = path.join(ROOT, 'output', 'xqcL_coin_textured.obj');
const OUT_MTL = path.join(ROOT, 'output', 'xqcL_coin_textured.mtl');

const EMOJI_URL = 'https://cdn.discordapp.com/emojis/898264218439131226.png?size=512&quality=lossless';

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
  // u,v in [0,1]
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
  // sRGB luma approx
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}

function buildCoinMesh({
  img,
  diameterMM = 60,
  baseThicknessMM = 3.0,
  reliefHeightMM = 1.6,
  rimWidthMM = 2.2,
  rimHeightMM = 0.8,
  segments = 256,
  rings = 128,
  emojiScale = 0.82, // fraction of inner diameter used for mapping the emoji
  reliefGamma = 1.15,
  minReliefMM = 0.05,
}) {
  const R = diameterMM / 2;
  const innerR = Math.max(0, R - rimWidthMM);

  const V = [];     // vertices [x,y,z]
  const VT = [];    // uvs [u,v] for OBJ

  function pushV(x, y, z) { V.push([x, y, z]); return V.length - 1; }
  function pushVT(u, v) { VT.push([u, v]); return VT.length - 1; }

  // vertex indexing helpers
  const topIndex = [];   // [ring][seg] -> vertex index (top)
  const botIndex = [];   // [ring][seg] -> vertex index (bottom)
  const topUV = [];      // [ring][seg] -> vt index

  // Build rings
  for (let ri = 0; ri <= rings; ri++) {
    const rr = (ri / rings) * R;

    if (ri === 0) {
      // center vertex
      const u = 0.5;
      const v = 0.5;
      const [r, g, b, a] = sampleRGBA_bilinear(img, u, v);
      const lum = luminance(r, g, b);
      const relief = Math.max(0, a) * Math.max(minReliefMM, Math.pow(lum, reliefGamma) * reliefHeightMM);
      const zTop = baseThicknessMM + relief;
      topIndex[0] = [pushV(0, 0, zTop)];
      botIndex[0] = [pushV(0, 0, 0)];
      topUV[0] = [pushVT(u, v)];
      continue;
    }

    topIndex[ri] = new Array(segments);
    botIndex[ri] = new Array(segments);
    topUV[ri] = new Array(segments);

    for (let si = 0; si < segments; si++) {
      const th = (si / segments) * Math.PI * 2;
      const x = rr * Math.cos(th);
      const y = rr * Math.sin(th);

      let zTop = baseThicknessMM;
      let u, v;

      if (rr >= innerR && rimWidthMM > 0) {
        // Rim area: keep it clean and flat, slightly raised.
        zTop = baseThicknessMM + rimHeightMM;
        // UVs still set reasonably.
        u = 0.5 + (x / (2 * innerR * emojiScale));
        v = 0.5 - (y / (2 * innerR * emojiScale));
      } else {
        // Emoji relief area.
        u = 0.5 + (x / (2 * innerR * emojiScale));
        v = 0.5 - (y / (2 * innerR * emojiScale));
        const [r, g, b, a] = sampleRGBA_bilinear(img, u, v);
        const lum = luminance(r, g, b);
        const relief = a * Math.max(minReliefMM, Math.pow(lum, reliefGamma) * reliefHeightMM);
        zTop = baseThicknessMM + relief;
      }

      topIndex[ri][si] = pushV(x, y, zTop);
      botIndex[ri][si] = pushV(x, y, 0);
      topUV[ri][si] = pushVT(clamp(u, 0, 1), clamp(v, 0, 1));
    }
  }

  const tris = []; // each tri: [a,b,c]

  function addTri(a, b, c) { tris.push([a, b, c]); }

  // Top surface
  // center fan to ring 1
  const cTop = topIndex[0][0];
  for (let s = 0; s < segments; s++) {
    const s1 = (s + 1) % segments;
    addTri(cTop, topIndex[1][s], topIndex[1][s1]);
  }
  // rings
  for (let r = 1; r < rings; r++) {
    for (let s = 0; s < segments; s++) {
      const s1 = (s + 1) % segments;
      const a = topIndex[r][s];
      const b = topIndex[r][s1];
      const c = topIndex[r + 1][s1];
      const d = topIndex[r + 1][s];
      addTri(a, d, c);
      addTri(a, c, b);
    }
  }

  // Bottom surface (reverse winding)
  const cBot = botIndex[0][0];
  for (let s = 0; s < segments; s++) {
    const s1 = (s + 1) % segments;
    addTri(cBot, botIndex[1][s1], botIndex[1][s]);
  }
  for (let r = 1; r < rings; r++) {
    for (let s = 0; s < segments; s++) {
      const s1 = (s + 1) % segments;
      const a = botIndex[r][s];
      const b = botIndex[r][s1];
      const c = botIndex[r + 1][s1];
      const d = botIndex[r + 1][s];
      addTri(a, c, d);
      addTri(a, b, c);
    }
  }

  // Side wall (outer ring)
  const rOut = rings;
  for (let s = 0; s < segments; s++) {
    const s1 = (s + 1) % segments;
    const a = botIndex[rOut][s];
    const b = botIndex[rOut][s1];
    const c = topIndex[rOut][s1];
    const d = topIndex[rOut][s];
    addTri(a, b, c);
    addTri(a, c, d);
  }

  return { V, tris, VT, topIndex, topUV, params: { diameterMM, baseThicknessMM, reliefHeightMM, rimWidthMM, rimHeightMM, segments, rings } };
}

function writeBinarySTL({ V, tris }, outPath) {
  const triCount = tris.length;
  const out = Buffer.alloc(84 + triCount * 50);
  out.write('xqcL coin STL', 0, 'ascii');
  out.writeUInt32LE(triCount, 80);
  let o = 84;

  function normal(a, b, c) {
    const [ax, ay, az] = V[a];
    const [bx, by, bz] = V[b];
    const [cx, cy, cz] = V[c];
    const ux = bx - ax, uy = by - ay, uz = bz - az;
    const vx = cx - ax, vy = cy - ay, vz = cz - az;
    let nx = uy * vz - uz * vy;
    let ny = uz * vx - ux * vz;
    let nz = ux * vy - uy * vx;
    const len = Math.hypot(nx, ny, nz) || 1;
    return [nx / len, ny / len, nz / len];
  }

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

function writeTexturedOBJ(mesh, objPath, mtlPath) {
  const { V, VT, tris, topIndex, topUV } = mesh;

  // Build a fast lookup for vt per vertex only for top vertices we created UVs for.
  const vtForV = new Map();
  for (let r = 0; r < topIndex.length; r++) {
    if (!topIndex[r]) continue;
    for (let s = 0; s < topIndex[r].length; s++) {
      const vi = topIndex[r][s];
      const vti = topUV[r][s];
      vtForV.set(vi, vti);
    }
  }

  const obj = [];
  obj.push(`# xqcL coin textured OBJ (top face UV mapped to source/xqcL.png)`);
  obj.push(`mtllib ${path.basename(mtlPath)}`);
  obj.push(`o xqcL_coin`);

  for (const [x, y, z] of V) obj.push(`v ${x.toFixed(6)} ${y.toFixed(6)} ${z.toFixed(6)}`);
  for (const [u, v] of VT) obj.push(`vt ${u.toFixed(6)} ${v.toFixed(6)}`);

  obj.push(`usemtl emoji`);

  // Faces: attach vt if present, else omit UV.
  for (const [a, b, c] of tris) {
    const ta = vtForV.get(a);
    const tb = vtForV.get(b);
    const tc = vtForV.get(c);
    if (ta != null && tb != null && tc != null) {
      // OBJ indices are 1-based
      obj.push(`f ${a + 1}/${ta + 1} ${b + 1}/${tb + 1} ${c + 1}/${tc + 1}`);
    } else {
      obj.push(`f ${a + 1} ${b + 1} ${c + 1}`);
    }
  }

  fs.writeFileSync(objPath, obj.join('\n') + '\n');

  const mtl = [];
  mtl.push(`# xqcL coin material`);
  mtl.push(`newmtl emoji`);
  mtl.push(`Ka 1.000 1.000 1.000`);
  mtl.push(`Kd 1.000 1.000 1.000`);
  mtl.push(`Ks 0.000 0.000 0.000`);
  mtl.push(`d 1.0`);
  mtl.push(`illum 1`);
  mtl.push(`map_Kd ../source/xqcL.png`);
  fs.writeFileSync(mtlPath, mtl.join('\n') + '\n');
}

async function main() {
  ensureDir(path.join(ROOT, 'source'));
  ensureDir(path.join(ROOT, 'output'));

  await downloadIfMissing(EMOJI_URL, SOURCE_PNG);

  const img = PNG.sync.read(fs.readFileSync(SOURCE_PNG));

  const mesh = buildCoinMesh({ img });

  writeBinarySTL(mesh, OUT_STL);
  writeTexturedOBJ(mesh, OUT_OBJ, OUT_MTL);

  const st = fs.statSync(OUT_STL);
  console.log(`Wrote ${OUT_STL} (${st.size} bytes)`);
  console.log(`Triangles: ${mesh.tris.length}`);
  console.log(`Wrote ${OUT_OBJ}`);
}

main().catch((e) => { console.error(e); process.exit(1); });
