# xqcL → 3D (STL)

This folder contains a reproducible pipeline to turn the Discord **xqcL** custom emoji into a **watertight 3D STL** suitable for printing/CAD import.

## Output

- `output/xqcL_relief_60mm.stl` — bas-relief (heightmap) generated from the emoji alpha mask.

## Generate

```bash
cd Friendenklup/xqcL-3d
npm install
npm run build
```

## What this does (practical method we implemented)

We download the emoji PNG from Discord’s CDN and convert **alpha → height** to create a 3D *bas‑relief*:
- transparent pixels → 0 height
- opaque pixels → max relief height
- adds a solid base + side walls → watertight solid STL

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
