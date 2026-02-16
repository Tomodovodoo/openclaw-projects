#!/usr/bin/env python3
import json
import os
import struct
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "output" / "xqcL_coin_P1S_AMS.3mf"
PARTS_DIR = ROOT / "output" / "print_parts"
PALETTE_JSON = PARTS_DIR / "palette.json"

NS = "http://schemas.microsoft.com/3dmanufacturing/core/2015/02"
RELNS = "http://schemas.openxmlformats.org/package/2006/relationships"
CTNS = "http://schemas.openxmlformats.org/package/2006/content-types"


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
        ia = vmap.get(key(a))
        if ia is None:
            ia = len(vertices)
            vmap[key(a)] = ia
            vertices.append(a)
        ib = vmap.get(key(b))
        if ib is None:
            ib = len(vertices)
            vmap[key(b)] = ib
            vertices.append(b)
        ic = vmap.get(key(c))
        if ic is None:
            ic = len(vertices)
            vmap[key(c)] = ic
            vertices.append(c)
        triangles.append((ia, ib, ic))

    return vertices, triangles


def content_types_xml():
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="{CTNS}">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>
</Types>
'''


def rels_xml():
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="{RELNS}">
  <Relationship Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel" Target="/3D/3dmodel.model"/>
</Relationships>
'''


def model_xml(objects, basemats):
    # basemats: list of dict {name, color}
    # objects: list of dict {id, name, vertices, triangles, mat_index}

    bm_lines = [f'  <basematerials id="1">']
    for bm in basemats:
        name = escape(bm["name"])
        color = bm["color"]
        bm_lines.append(f'    <base name="{name}" displaycolor="{color}"/>')
    bm_lines.append('  </basematerials>')

    res_lines = ['<resources>']
    res_lines.extend(bm_lines)

    for obj in objects:
        res_lines.append(f'  <object id="{obj["id"]}" name="{escape(obj["name"])}" type="model">')
        res_lines.append('    <mesh>')
        res_lines.append('      <vertices>')
        for (x, y, z) in obj["vertices"]:
            res_lines.append(f'        <vertex x="{x:.6f}" y="{y:.6f}" z="{z:.6f}"/>')
        res_lines.append('      </vertices>')
        res_lines.append('      <triangles>')
        mi = obj["mat_index"]
        for (v1, v2, v3) in obj["triangles"]:
            # assign material by setting p1/p2/p3 to same base material index
            res_lines.append(f'        <triangle v1="{v1}" v2="{v2}" v3="{v3}" pid="1" p1="{mi}" p2="{mi}" p3="{mi}"/>')
        res_lines.append('      </triangles>')
        res_lines.append('    </mesh>')
        res_lines.append('  </object>')

    res_lines.append('</resources>')

    build_lines = ['<build>']
    for obj in objects:
        # identity transform
        build_lines.append(f'  <item objectid="{obj["id"]}"/>')
    build_lines.append('</build>')

    return f'''<?xml version="1.0" encoding="UTF-8"?>
<model xmlns="{NS}" unit="millimeter">
{os.linesep.join(res_lines)}
{os.linesep.join(build_lines)}
</model>
'''


def main():
    PARTS_DIR.mkdir(parents=True, exist_ok=True)

    # Ensure parts exist
    required = [
        PARTS_DIR / "xqcL_coin_base_60mm.stl",
        PARTS_DIR / "xqcL_coin_color_0.stl",
        PARTS_DIR / "xqcL_coin_color_1.stl",
        PARTS_DIR / "xqcL_coin_color_2.stl",
        PARTS_DIR / "xqcL_coin_color_3.stl",
        PALETTE_JSON,
    ]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        raise SystemExit("Missing required files; run `npm run build:parts` first. Missing: " + ", ".join(missing))

    palette = json.loads(PALETTE_JSON.read_text("utf-8"))
    pal = palette["palette"]

    # Base material list: 4 palette colors + a neutral base
    basemats = []
    for i, c in enumerate(pal):
        basemats.append({"name": f"color_{i}", "color": c["hex"]})
    basemats.append({"name": "base", "color": "#D0D0D0"})

    parts = [
        ("base", PARTS_DIR / "xqcL_coin_base_60mm.stl", 4),
        ("color_0", PARTS_DIR / "xqcL_coin_color_0.stl", 0),
        ("color_1", PARTS_DIR / "xqcL_coin_color_1.stl", 1),
        ("color_2", PARTS_DIR / "xqcL_coin_color_2.stl", 2),
        ("color_3", PARTS_DIR / "xqcL_coin_color_3.stl", 3),
    ]

    objects = []
    next_id = 2
    for name, stl_path, mat_index in parts:
        tris = read_binary_stl(stl_path)
        verts, tri_idx = stl_to_indexed_mesh(tris)
        objects.append({
            "id": next_id,
            "name": name,
            "vertices": verts,
            "triangles": tri_idx,
            "mat_index": mat_index,
        })
        next_id += 1

    model = model_xml(objects, basemats)

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
