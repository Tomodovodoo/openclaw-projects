import fs from 'node:fs';

function readBinarySTL(buf) {
  const triCount = buf.readUInt32LE(80);
  let o = 84;
  let minX = Infinity, minY = Infinity, minZ = Infinity;
  let maxX = -Infinity, maxY = -Infinity, maxZ = -Infinity;

  for (let t = 0; t < triCount; t++) {
    // skip normal
    o += 12;
    for (let v = 0; v < 3; v++) {
      const x = buf.readFloatLE(o); const y = buf.readFloatLE(o + 4); const z = buf.readFloatLE(o + 8);
      minX = Math.min(minX, x); minY = Math.min(minY, y); minZ = Math.min(minZ, z);
      maxX = Math.max(maxX, x); maxY = Math.max(maxY, y); maxZ = Math.max(maxZ, z);
      o += 12;
    }
    // attribute
    o += 2;
  }
  return { triCount, bbox: { minX, minY, minZ, maxX, maxY, maxZ } };
}

const stlPath = process.argv[2];
if (!stlPath) {
  console.error('Usage: node inspect_stl.js <file.stl>');
  process.exit(2);
}

const buf = fs.readFileSync(stlPath);
const { triCount, bbox } = readBinarySTL(buf);
const dx = bbox.maxX - bbox.minX;
const dy = bbox.maxY - bbox.minY;
const dz = bbox.maxZ - bbox.minZ;

console.log(`File: ${stlPath}`);
console.log(`Triangles: ${triCount}`);
console.log(`BBox X: ${bbox.minX.toFixed(3)} .. ${bbox.maxX.toFixed(3)} (Δ ${dx.toFixed(3)} mm)`);
console.log(`BBox Y: ${bbox.minY.toFixed(3)} .. ${bbox.maxY.toFixed(3)} (Δ ${dy.toFixed(3)} mm)`);
console.log(`BBox Z: ${bbox.minZ.toFixed(3)} .. ${bbox.maxZ.toFixed(3)} (Δ ${dz.toFixed(3)} mm)`);
console.log(`Approx diameter: ${Math.max(dx, dy).toFixed(3)} mm`);
