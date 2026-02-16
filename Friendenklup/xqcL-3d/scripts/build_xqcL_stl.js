import fs from 'node:fs';
import path from 'node:path';
import { PNG } from 'pngjs';

const ROOT = path.resolve(path.dirname(new URL(import.meta.url).pathname), '..');
const SOURCE_PNG = path.join(ROOT, 'source', 'xqcL.png');
const OUT_STL = path.join(ROOT, 'output', 'xqcL_relief_60mm.stl');

const EMOJI_URL = 'https://cdn.discordapp.com/emojis/898264218439131226.png?size=512&quality=lossless';

function ensureDir(p) {
  fs.mkdirSync(p, { recursive: true });
}

function downloadIfMissing(url, outPath) {
  if (fs.existsSync(outPath)) return;
  // Node 18+ has fetch.
  return fetch(url).then(async (res) => {
    if (!res.ok) throw new Error(`download failed: ${res.status} ${res.statusText}`);
    const ab = await res.arrayBuffer();
    fs.writeFileSync(outPath, Buffer.from(ab));
  });
}

function clamp(v, lo, hi) { return Math.max(lo, Math.min(hi, v)); }

function resampleNearestAlpha(alpha, w, h, newW, newH) {
  const out = new Float32Array(newW * newH);
  for (let y = 0; y < newH; y++) {
    const sy = Math.floor((y / (newH - 1)) * (h - 1));
    for (let x = 0; x < newW; x++) {
      const sx = Math.floor((x / (newW - 1)) * (w - 1));
      out[y * newW + x] = alpha[sy * w + sx];
    }
  }
  return out;
}

function buildWatertightHeightmapSTL({
  alpha, w, h,
  targetWidthMM = 60,
  baseThicknessMM = 2.0,
  reliefHeightMM = 6.0,
}) {
  // Coordinate system: X right, Y up, Z out of plane.
  const dx = targetWidthMM / (w - 1);
  const dy = targetWidthMM / (h - 1); // square output for simplicity

  const zTop = (i) => baseThicknessMM + (alpha[i] / 255) * reliefHeightMM;
  const zBot = 0.0;

  const triangles = [];

  function addTri(ax, ay, az, bx, by, bz, cx, cy, cz) {
    // Compute normal (not strictly necessary for most STL consumers, but nice).
    const ux = bx - ax, uy = by - ay, uz = bz - az;
    const vx = cx - ax, vy = cy - ay, vz = cz - az;
    let nx = uy * vz - uz * vy;
    let ny = uz * vx - ux * vz;
    let nz = ux * vy - uy * vx;
    const len = Math.hypot(nx, ny, nz) || 1;
    nx /= len; ny /= len; nz /= len;
    triangles.push({ nx, ny, nz, ax, ay, az, bx, by, bz, cx, cy, cz });
  }

  function V(x, y, z) {
    // center it around origin-ish for nicer imports
    const cx = (w - 1) * dx / 2;
    const cy = (h - 1) * dy / 2;
    return [x * dx - cx, y * dy - cy, z];
  }

  // Top surface
  for (let y = 0; y < h - 1; y++) {
    for (let x = 0; x < w - 1; x++) {
      const i00 = y * w + x;
      const i10 = y * w + (x + 1);
      const i01 = (y + 1) * w + x;
      const i11 = (y + 1) * w + (x + 1);

      const [x00, y00, z00] = V(x, y, zTop(i00));
      const [x10, y10, z10] = V(x + 1, y, zTop(i10));
      const [x01, y01, z01] = V(x, y + 1, zTop(i01));
      const [x11, y11, z11] = V(x + 1, y + 1, zTop(i11));

      // two triangles (counter-clockwise as viewed from +Z)
      addTri(x00, y00, z00, x10, y10, z10, x11, y11, z11);
      addTri(x00, y00, z00, x11, y11, z11, x01, y01, z01);
    }
  }

  // Bottom surface (flip winding)
  for (let y = 0; y < h - 1; y++) {
    for (let x = 0; x < w - 1; x++) {
      const [x00, y00, z00] = V(x, y, zBot);
      const [x10, y10, z10] = V(x + 1, y, zBot);
      const [x01, y01, z01] = V(x, y + 1, zBot);
      const [x11, y11, z11] = V(x + 1, y + 1, zBot);

      // reverse order
      addTri(x00, y00, z00, x11, y11, z11, x10, y10, z10);
      addTri(x00, y00, z00, x01, y01, z01, x11, y11, z11);
    }
  }

  // Side walls: connect top boundary to bottom boundary.
  // Each segment -> two triangles.
  function addWall(x0, y0, x1, y1, zTop0, zTop1) {
    const [ax, ay, az] = V(x0, y0, zBot);
    const [bx, by, bz] = V(x1, y1, zBot);
    const [cx, cy, cz] = V(x1, y1, zTop1);
    const [dx_, dy_, dz_] = V(x0, y0, zTop0);

    // outward winding depends on edge; this is generally fine for printing.
    addTri(ax, ay, az, bx, by, bz, cx, cy, cz);
    addTri(ax, ay, az, cx, cy, cz, dx_, dy_, dz_);
  }

  // top edge y=0
  for (let x = 0; x < w - 1; x++) {
    const i0 = 0 * w + x;
    const i1 = 0 * w + (x + 1);
    addWall(x, 0, x + 1, 0, zTop(i0), zTop(i1));
  }
  // bottom edge y=h-1
  for (let x = 0; x < w - 1; x++) {
    const i0 = (h - 1) * w + x;
    const i1 = (h - 1) * w + (x + 1);
    // reverse segment to roughly keep outward normals
    addWall(x + 1, h - 1, x, h - 1, zTop(i1), zTop(i0));
  }
  // left edge x=0
  for (let y = 0; y < h - 1; y++) {
    const i0 = y * w + 0;
    const i1 = (y + 1) * w + 0;
    // reverse to keep outward-ish
    addWall(0, y + 1, 0, y, zTop(i1), zTop(i0));
  }
  // right edge x=w-1
  for (let y = 0; y < h - 1; y++) {
    const i0 = y * w + (w - 1);
    const i1 = (y + 1) * w + (w - 1);
    addWall(w - 1, y, w - 1, y + 1, zTop(i0), zTop(i1));
  }

  return triangles;
}

function writeBinarySTL(tris, outPath) {
  const triCount = tris.length;
  const out = Buffer.alloc(84 + triCount * 50);
  // 80-byte header
  out.write('xqcL heightmap relief STL', 0, 'ascii');
  out.writeUInt32LE(triCount, 80);

  let o = 84;
  for (const t of tris) {
    out.writeFloatLE(t.nx, o + 0);
    out.writeFloatLE(t.ny, o + 4);
    out.writeFloatLE(t.nz, o + 8);

    out.writeFloatLE(t.ax, o + 12);
    out.writeFloatLE(t.ay, o + 16);
    out.writeFloatLE(t.az, o + 20);

    out.writeFloatLE(t.bx, o + 24);
    out.writeFloatLE(t.by, o + 28);
    out.writeFloatLE(t.bz, o + 32);

    out.writeFloatLE(t.cx, o + 36);
    out.writeFloatLE(t.cy, o + 40);
    out.writeFloatLE(t.cz, o + 44);

    out.writeUInt16LE(0, o + 48); // attribute byte count
    o += 50;
  }

  fs.writeFileSync(outPath, out);
}

async function main() {
  ensureDir(path.join(ROOT, 'source'));
  ensureDir(path.join(ROOT, 'output'));

  await downloadIfMissing(EMOJI_URL, SOURCE_PNG);

  const png = PNG.sync.read(fs.readFileSync(SOURCE_PNG));
  const { width, height, data } = png;

  // Extract alpha as grayscale height source
  const alpha = new Uint8Array(width * height);
  for (let i = 0; i < width * height; i++) alpha[i] = data[i * 4 + 3];

  // Make it a bit higher-res for smoother edges.
  const W = 256, H = 256;
  const a2 = resampleNearestAlpha(alpha, width, height, W, H);

  // Convert Float32 alpha back to 0..255 Uint8
  const a2u = new Uint8Array(W * H);
  for (let i = 0; i < a2u.length; i++) a2u[i] = clamp(Math.round(a2[i]), 0, 255);

  const tris = buildWatertightHeightmapSTL({
    alpha: a2u,
    w: W,
    h: H,
    targetWidthMM: 60,
    baseThicknessMM: 2.0,
    reliefHeightMM: 6.0,
  });

  writeBinarySTL(tris, OUT_STL);

  const stat = fs.statSync(OUT_STL);
  console.log(`Wrote ${OUT_STL}`);
  console.log(`Triangles: ${tris.length}`);
  console.log(`Size: ${stat.size} bytes`);
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
