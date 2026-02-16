#!/usr/bin/env python3
"""Build a *colored* 3MF that Bambu Studio will actually display as multi-color.

Important: Bambu Studio’s importer (see bbs_3mf.cpp) recognizes colors via:
- <m:colorgroup id=...><m:color color="#RRGGBB"/></m:colorgroup>
- per-object pid/pindex (or per-triangle pid/p1/p2/p3)

It does NOT reliably use the 3MF Materials Extension <basematerials> for coloring.

This script packages our watertight STL parts into a single 3MF with an assembly object.
"""

import os
import struct
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "output" / "xqcL_coin_P1S_AMS_colored.3mf"
PARTS_DIR = ROOT / "output" / "print_parts"

# Filament colors requested (approximate display colors)
COLORS = {
    "black": "#000000",
    "white": "#FFFFFF",
    "red":   "#D40000",
    "wood":  "#C8A06A",
}

# 3MF namespaces
NS_CORE = "http://schemas.microsoft.com/3dmanufacturing/core/2015/02"
NS_M    = "http://schemas.microsoft.com/3dmanufacturing/material/2015/02"  # prefix m
NS_REL  = "http://schemas.openxmlformats.org/package/2006/relationships"
NS_CT   = "http://schemas.openxmlformats.org/package/2006/content-types"


def read_binary_stl(path: Path):
    b = path.read_bytes()
    tri_count = struct.unpack_from('<I', b, 80)[0]
    o = 84
    tris = []
    for _ in range(tri_count):
        o += 12  # normal
        v = []
        for __ in range(3):
            x, y, z = struct.unpack_from('<fff', b, o)
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
        return (round(p[0], round_decimals), round(p[1], round_decimals), round(p[2], round_decimals))

    for (a, b, c) in tris:
        ka, kb, kc = key(a), key(b), key(c)
        ia = vmap.get(ka)
        if ia is None:
            ia = len(vertices); vmap[ka] = ia; vertices.append(a)
        ib = vmap.get(kb)
        if ib is None:
            ib = len(vertices); vmap[kb] = ib; vertices.append(b)
        ic = vmap.get(kc)
        if ic is None:
            ic = len(vertices); vmap[kc] = ic; vertices.append(c)
        triangles.append((ia, ib, ic))

    return vertices, triangles


def content_types_xml():
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="{NS_CT}">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>
</Types>
'''


def rels_xml():
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="{NS_REL}">
  <Relationship Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel" Target="/3D/3dmodel.model"/>
</Relationships>
'''


def model_xml(objects, assembly_object_id: int):
    # Color group id=1 with 4 color entries.
    colorgroup = [
        f'  <m:colorgroup id="1">',
        f'    <m:color color="{COLORS["black"]}"/>',
        f'    <m:color color="{COLORS["white"]}"/>',
        f'    <m:color color="{COLORS["red"]}"/>',
        f'    <m:color color="{COLORS["wood"]}"/>',
        f'  </m:colorgroup>',
    ]

    res_lines = ['<resources>']
    res_lines.extend(colorgroup)

    # Part objects with pid/pindex so Bambu can color them.
    for obj in objects:
        res_lines.append(
            f'  <object id="{obj["id"]}" name="{escape(obj["name"])}" type="model" pid="1" pindex="{obj["pindex"]}">'  # pid=1 -> colorgroup id 1
        )
        res_lines.append('    <mesh>')
        res_lines.append('      <vertices>')
        for (x, y, z) in obj["vertices"]:
            res_lines.append(f'        <vertex x="{x:.6f}" y="{y:.6f}" z="{z:.6f}"/>')
        res_lines.append('      </vertices>')
        res_lines.append('      <triangles>')
        for (v1, v2, v3) in obj["triangles"]:
            # No need to set pid/p1/p2/p3 per-triangle: importer will fallback to object pid/pindex.
            res_lines.append(f'        <triangle v1="{v1}" v2="{v2}" v3="{v3}"/>')
        res_lines.append('      </triangles>')
        res_lines.append('    </mesh>')
        res_lines.append('  </object>')

    # Assembly object grouping the parts into one model item.
    res_lines.append(f'  <object id="{assembly_object_id}" name="xqcL_coin" type="model">')
    res_lines.append('    <components>')
    for obj in objects:
        res_lines.append(f'      <component objectid="{obj["id"]}"/>')
    res_lines.append('    </components>')
    res_lines.append('  </object>')

    res_lines.append('</resources>')

    build_lines = ['<build>']
    build_lines.append(f'  <item objectid="{assembly_object_id}"/>')
    build_lines.append('</build>')

    return f'''<?xml version="1.0" encoding="UTF-8"?>
<model xmlns="{NS_CORE}" xmlns:m="{NS_M}" unit="millimeter">
{os.linesep.join(res_lines)}
{os.linesep.join(build_lines)}
</model>
'''


def main():
    parts = [
        ("base_black", PARTS_DIR / "xqcL_coin_base_60mm.stl", 0),
        ("inlay_white", PARTS_DIR / "xqcL_coin_inlay_white.stl", 1),
        ("inlay_red",   PARTS_DIR / "xqcL_coin_inlay_red.stl",   2),
        ("inlay_wood",  PARTS_DIR / "xqcL_coin_inlay_wood.stl",  3),
    ]

    missing = [str(p) for _, p, _ in parts if not p.exists()]
    if missing:
        raise SystemExit("Missing required STL parts; run `npm run build:parts` first. Missing: " + ", ".join(missing))

    objects = []
    next_id = 2
    for name, stl_path, pindex in parts:
        tris = read_binary_stl(stl_path)
        verts, tri_idx = stl_to_indexed_mesh(tris)
        objects.append({
            "id": next_id,
            "name": name,
            "vertices": verts,
            "triangles": tri_idx,
            "pindex": pindex,
        })
        next_id += 1

    assembly_object_id = next_id
    model = model_xml(objects, assembly_object_id)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    if OUT.exists():
        OUT.unlink()

    with zipfile.ZipFile(OUT, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        z.writestr("[Content_Types].xml", content_types_xml())
        z.writestr("_rels/.rels", rels_xml())
        z.writestr("3D/3dmodel.model", model)

    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
