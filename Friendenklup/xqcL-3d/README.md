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
# optional: multi-part color print assets (best for AMS/MMU)
npm run build:parts
# single-file 3MFs for Bambu P1S + AMS (open in Bambu Studio)
npm run build:p1s
# outputs:
#   output/xqcL_coin_P1S_AMS_BambuProject.3mf      (best: avoids the “not from bambu lab” warning; sets per-part extruders)
#   output/xqcL_coin_P1S_AMS_colored.3mf           (generic colored 3MF; 4 separate build items)
#   output/xqcL_coin_P1S_AMS_colored_assembly.3mf  (generic colored 3MF; single build item via components)
```

## 3MF color encoding note (why Bambu Studio shows colors)

The generated 3MF uses the 3MF Material Extension **colorgroup** and assigns
colors on **each triangle** (`pid` + `p1/p2/p3`). This is the most reliable way
we found to make Bambu Studio import the file as **multi-color / multi-part**.

If Bambu Studio shows the warning:
> "The 3mf file is not from bambu lab, load geometry data only"

…use the Bambu project variant (it includes Bambu metadata + `model_settings.config` so parts load as multiple extruders):
- `xqcL_coin_P1S_AMS_BambuProject.3mf`

If your slicer still imports as a single material, try the generic variants:
- `xqcL_coin_P1S_AMS_colored.3mf` (4 separate build items)
- `xqcL_coin_P1S_AMS_colored_assembly.3mf` (single build item via components)

## What this does (practical method we implemented)

We download the emoji PNG from Discord’s CDN and generate a **coin**:
- circular base + rim (watertight) + a small blend zone so the rim transition isn’t razor-sharp
- **embossed relief** derived from the emoji’s **luminance** (for facial detail) and **alpha** (for clean edges)
- also emits a **textured OBJ** so the *colors are exactly the emoji* in 3D viewers

This is fast, deterministic, and works without Blender.

## Multicolor printing (recommended modern approach)

**Best practical path today:** import **multi-part** STLs and assign colors by part (AMS/MMU).

After running `npm run build:parts` you get:
- `output/print_parts/xqcL_coin_base_60mm.stl` (intended filament: **black**)
- `output/print_parts/xqcL_coin_inlay_white.stl`
- `output/print_parts/xqcL_coin_inlay_red.stl`
- `output/print_parts/xqcL_coin_inlay_wood.stl`
- `output/print_parts/palette.json`

The inlays are generated as **constant-height** watertight solids. Relief/detail is in the single-material coin STL; the inlays are for **spot-color printing** (AMS/MMU).

In Bambu Studio / PrusaSlicer:
1) Import the base STL
2) Import the color STLs as **parts of the same object** (merge)
3) Assign a filament to each part

This avoids relying on textured-model import support (which is still inconsistent).

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
