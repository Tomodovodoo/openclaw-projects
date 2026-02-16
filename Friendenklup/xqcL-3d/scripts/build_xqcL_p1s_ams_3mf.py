#!/usr/bin/env python3
"""Build *colored* 3MFs for Bambu Studio (P1S + AMS).

Why this exists
--------------
Bambu Studio does not reliably show colors when a 3MF only uses the Materials
Extension (<basematerials>). In practice it is much more consistent to use the
3MF Material "colorgroup" resource and assign colors via *triangle-level*
properties:

    <m:colorgroup id="1"> ... </m:colorgroup>
    <triangle ... pid="1" p1="<idx>" p2="<idx>" p3="<idx>" />

Where pid references the colorgroup id and p1/p2/p3 are indices within it.

We also generate two build layouts because some slicers differ in how they
handle component assemblies:
- "items" build: 4 separate build items (recommended for Bambu Studio)
- "assembly" build: 1 build item referencing an assembly object with components

Outputs
-------
- output/xqcL_coin_P1S_AMS_colored.3mf (generic colored 3MF; items build)
- output/xqcL_coin_P1S_AMS_colored_assembly.3mf (generic colored 3MF; components assembly build)
- output/xqcL_coin_P1S_AMS_BambuProject.3mf (BambuStudio-recognized project 3MF: avoids the
  "not from bambu lab" warning and sets per-part extruders for AMS)
"""

import os
import struct
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent
PARTS_DIR = ROOT / "output" / "print_parts"

OUT_ITEMS = ROOT / "output" / "xqcL_coin_P1S_AMS_colored.3mf"
OUT_ASSEMBLY = ROOT / "output" / "xqcL_coin_P1S_AMS_colored_assembly.3mf"
# BambuStudio-recognized project 3MF with explicit per-part extruder assignment.
OUT_BAMBU_PROJECT = ROOT / "output" / "xqcL_coin_P1S_AMS_BambuProject.3mf"

# Filament colors requested (approximate display colors)
COLORS = {
    "black": "#000000",
    "white": "#FFFFFF",
    "red": "#D40000",
    "wood": "#C8A06A",
}

# 3MF namespaces
NS_CORE = "http://schemas.microsoft.com/3dmanufacturing/core/2015/02"
NS_M = "http://schemas.microsoft.com/3dmanufacturing/material/2015/02"  # prefix m
NS_REL = "http://schemas.openxmlformats.org/package/2006/relationships"
NS_CT = "http://schemas.openxmlformats.org/package/2006/content-types"
# Bambu's 3MFs add this namespace on the <model> element.
NS_BAMBU = "http://schemas.bambulab.com/package/2021"


def read_binary_stl(path: Path):
    b = path.read_bytes()
    tri_count = struct.unpack_from("<I", b, 80)[0]
    o = 84
    tris = []
    for _ in range(tri_count):
        o += 12  # normal
        v = []
        for __ in range(3):
            x, y, z = struct.unpack_from("<fff", b, o)
            o += 12
            v.append((x, y, z))
        o += 2
        tris.append(tuple(v))
    return tris


def stl_to_indexed_mesh(tris, round_decimals=6):
    vmap = {}
    vertices = []
    triangles = []

    def key(p):
        return (
            round(p[0], round_decimals),
            round(p[1], round_decimals),
            round(p[2], round_decimals),
        )

    for (a, b, c) in tris:
        ka, kb, kc = key(a), key(b), key(c)
        ia = vmap.get(ka)
        if ia is None:
            ia = len(vertices)
            vmap[ka] = ia
            vertices.append(a)
        ib = vmap.get(kb)
        if ib is None:
            ib = len(vertices)
            vmap[kb] = ib
            vertices.append(b)
        ic = vmap.get(kc)
        if ic is None:
            ic = len(vertices)
            vmap[kc] = ic
            vertices.append(c)
        triangles.append((ia, ib, ic))

    return vertices, triangles


def content_types_xml():
    return f"""<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<Types xmlns=\"{NS_CT}\">
  <Default Extension=\"rels\" ContentType=\"application/vnd.openxmlformats-package.relationships+xml\"/>
  <Default Extension=\"model\" ContentType=\"application/vnd.ms-package.3dmanufacturing-3dmodel+xml\"/>
</Types>
"""


def rels_xml():
    return f"""<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<Relationships xmlns=\"{NS_REL}\">
  <Relationship Id=\"rel0\" Type=\"http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel\" Target=\"/3D/3dmodel.model\"/>
</Relationships>
"""


def model_xml(objects, build_mode: str, *, bambu_meta: bool = False, assembly_object_id: int | None = None):
    """Return 3D/3dmodel.model XML.

    build_mode:
      - "items": separate <build><item objectid=.../></build>
      - "assembly": build references a components assembly object

    bambu_meta:
      If True, embed the metadata Bambu Studio uses to decide a 3MF is
      "from Bambu Lab" (otherwise it may show:
      "The 3mf file is not from bambu lab, load geometry data only").
    """

    # Color group id=1 with 4 color entries.
    colorgroup = [
        '  <m:colorgroup id="1">',
        f'    <m:color color="{COLORS["black"]}"/>',
        f'    <m:color color="{COLORS["white"]}"/>',
        f'    <m:color color="{COLORS["red"]}"/>',
        f'    <m:color color="{COLORS["wood"]}"/>',
        '  </m:colorgroup>',
    ]

    res_lines = ["<resources>"]
    res_lines.extend(colorgroup)

    # Part objects. Keep pid/pindex on the object, but do NOT rely on it;
    # Bambu Studio is much more consistent when triangles carry pid+p1/p2/p3.
    for obj in objects:
        pindex = int(obj["pindex"])
        res_lines.append(
            f'  <object id="{obj["id"]}" name="{escape(obj["name"])}" type="model" pid="1" pindex="{pindex}">'  # pid=1 -> colorgroup id 1
        )
        res_lines.append("    <mesh>")
        res_lines.append("      <vertices>")
        for (x, y, z) in obj["vertices"]:
            res_lines.append(f'        <vertex x="{x:.6f}" y="{y:.6f}" z="{z:.6f}"/>')
        res_lines.append("      </vertices>")
        res_lines.append("      <triangles>")
        for (v1, v2, v3) in obj["triangles"]:
            # Triangle-level color assignment (most compatible):
            # pid -> colorgroup id, p1/p2/p3 -> indices within the colorgroup.
            res_lines.append(
                f'        <triangle v1="{v1}" v2="{v2}" v3="{v3}" pid="1" p1="{pindex}" p2="{pindex}" p3="{pindex}"/>'
            )
        res_lines.append("      </triangles>")
        res_lines.append("    </mesh>")
        res_lines.append("  </object>")

    effective_assembly_id = None
    if build_mode == "assembly":
        effective_assembly_id = (
            int(assembly_object_id)
            if assembly_object_id is not None
            else max(obj["id"] for obj in objects) + 1
        )
        res_lines.append(
            f'  <object id="{effective_assembly_id}" name="xqcL_coin" type="model">'
        )
        res_lines.append("    <components>")
        for obj in objects:
            res_lines.append(f'      <component objectid="{obj["id"]}"/>')
        res_lines.append("    </components>")
        res_lines.append("  </object>")

    res_lines.append("</resources>")

    build_lines = ["<build>"]
    if build_mode == "items":
        for obj in objects:
            build_lines.append(f'  <item objectid="{obj["id"]}"/>')
    elif build_mode == "assembly":
        build_lines.append(f'  <item objectid="{effective_assembly_id}"/>')
    else:
        raise ValueError(f"Unknown build_mode: {build_mode}")
    build_lines.append("</build>")

    meta_lines: list[str] = []
    if bambu_meta:
        # This is the key signal used by Bambu Studio’s importer to treat a 3MF
        # as a Bambu-generated project.
        #
        # IMPORTANT: Newer Bambu Studio builds may refuse to load config from
        # very old generator versions and fall back to geometry-only import.
        # So we use a modern-looking 4-part version string (matching files
        # shipped in the BambuStudio repo resources).
        meta_lines.append('  <metadata name="Application">BambuStudio-02.00.02.01</metadata>')
        meta_lines.append('  <metadata name="BambuStudio:3mfVersion">1</metadata>')

    # Bambu adds xmlns:BambuStudio in its own exports. It doesn't hurt to include.
    bambu_ns = f' xmlns:BambuStudio="{NS_BAMBU}"' if bambu_meta else ""

    # requiredextensions improves compatibility with slicers that ignore
    # material properties unless explicitly declared.
    return f"""<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<model xmlns=\"{NS_CORE}\" xmlns:m=\"{NS_M}\"{bambu_ns} unit=\"millimeter\" requiredextensions=\"m\">
{os.linesep.join(meta_lines)}
{os.linesep.join(res_lines)}
{os.linesep.join(build_lines)}
</model>
"""


def write_3mf(
    out_path: Path, model_xml_str: str, *, extra_files: dict[str, str] | None = None
):
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if out_path.exists():
        out_path.unlink()

    with zipfile.ZipFile(
        out_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9
    ) as z:
        z.writestr("[Content_Types].xml", content_types_xml())
        z.writestr("_rels/.rels", rels_xml())
        z.writestr("3D/3dmodel.model", model_xml_str)
        if extra_files:
            for path, content in extra_files.items():
                z.writestr(path, content)


def model_settings_config_xml(parent_object_id: int, part_objects: list[dict]) -> str:
    """Minimal BambuStudio model_settings.config.

    This is where we can set per-part config like the default extruder.

    Format is Bambu/Prusa-style: <config><object id=...><part id=...> <metadata key=... value=.../>

    We intentionally keep this minimal so Bambu Studio will load it without
    needing a full printer/print profile embedded.
    """

    lines: list[str] = []
    lines.append('<?xml version="1.0" encoding="UTF-8"?>')
    lines.append('<config>')
    lines.append(f'  <object id="{parent_object_id}">')
    for obj in part_objects:
        # Map our 0-based colorgroup index to 1-based extruder index.
        extruder = int(obj["pindex"]) + 1
        name = escape(obj["name"])
        lines.append(f'    <part id="{obj["id"]}" subtype="model_part">')
        lines.append(f'      <metadata key="name" value="{name}"/>')
        lines.append(f'      <metadata key="extruder" value="{extruder}"/>')
        lines.append('    </part>')
    lines.append('  </object>')
    lines.append('</config>')
    lines.append('')
    return "\n".join(lines)


def main():
    parts = [
        ("base_black", PARTS_DIR / "xqcL_coin_base_60mm.stl", 0),
        ("inlay_white", PARTS_DIR / "xqcL_coin_inlay_white.stl", 1),
        ("inlay_red", PARTS_DIR / "xqcL_coin_inlay_red.stl", 2),
        ("inlay_wood", PARTS_DIR / "xqcL_coin_inlay_wood.stl", 3),
    ]

    missing = [str(p) for _, p, _ in parts if not p.exists()]
    if missing:
        raise SystemExit(
            "Missing required STL parts; run `npm run build:parts` first. Missing: "
            + ", ".join(missing)
        )

    objects = []
    next_id = 2
    for name, stl_path, pindex in parts:
        tris = read_binary_stl(stl_path)
        verts, tri_idx = stl_to_indexed_mesh(tris)
        objects.append(
            {
                "id": next_id,
                "name": name,
                "vertices": verts,
                "triangles": tri_idx,
                "pindex": pindex,
            }
        )
        next_id += 1

    write_3mf(OUT_ITEMS, model_xml(objects, build_mode="items"))
    write_3mf(OUT_ASSEMBLY, model_xml(objects, build_mode="assembly"))

    # BambuStudio-recognized project variant: adds Bambu metadata + model_settings.config
    # so the parts load as multiple extruders instead of "geometry only".
    assembly_id = max(obj["id"] for obj in objects) + 1
    bambu_model = model_xml(
        objects,
        build_mode="assembly",
        bambu_meta=True,
        assembly_object_id=assembly_id,
    )
    bambu_cfg = model_settings_config_xml(assembly_id, objects)
    write_3mf(
        OUT_BAMBU_PROJECT,
        bambu_model,
        extra_files={
            "Metadata/model_settings.config": bambu_cfg,
        },
    )

    print(f"Wrote {OUT_ITEMS}")
    print(f"Wrote {OUT_ASSEMBLY}")
    print(f"Wrote {OUT_BAMBU_PROJECT}")


if __name__ == "__main__":
    main()
