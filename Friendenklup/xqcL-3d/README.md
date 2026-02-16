# xqcL → 3D (STL)

This folder contains a reproducible pipeline to turn the Discord **xqcL** custom emoji into a **watertight 3D STL** suitable for printing/CAD import.

## Output

- `output/xqcL_coin_60mm.stl` — **3D printable coin** (circular, rim, embossed bas‑relief derived from emoji luminance + alpha).
- `output/xqcL_coin_textured.obj` + `output/xqcL_coin_textured.mtl` — textured render/preview model using the original emoji PNG.
- `output/xqcL_relief_60mm.stl` — legacy square bas‑relief from alpha only.

## Generate

```bash
cd Friendenklup/xqcL-3d
npm install
npm run build
npm run inspect:coin
```

## What this does (practical method we implemented)

We download the emoji PNG from Discord’s CDN and generate a **coin**:
- circular base + rim (watertight) + a small blend zone so the rim transition isn’t razor-sharp
- **embossed relief** derived from the emoji’s **luminance** (for facial detail) and **alpha** (for clean edges)
- also emits a **textured OBJ** so the *colors are exactly the emoji* in 3D viewers

This is fast, deterministic, and works without Blender.

## Modern alternatives (if you want a full 3D “figurine” model)

1) **Single-image → 3D (AI reconstruction)**
   - Tools/models: **TripoSR**, **Stable Fast 3D**, commercial services like Meshy/Luma/etc.
   - Pros: can produce a full 3D mesh with depth from one image.
   - Cons: needs GPU and/or paid services; results vary, often requires cleanup.

2) **Vector → extrude (clean logo-style model)**
   - PNG → SVG (trace) → extrude in **Blender** / CAD.
   - Pros: crisp edges, controllable bevels.
   - Cons: needs Inkscape/potrace/Blender; tracing can be fiddly.

3) **Heightmap relief (this repo)**
   - Pros: simple, reliable, great for “badge”/keychain/coin prints.
   - Cons: it’s a relief (not a full volumetric character).
