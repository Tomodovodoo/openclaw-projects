#!/usr/bin/env python3
"""Sanity-check that a 3MF encodes per-triangle colors via colorgroup.

Usage:
  python3 scripts/check_3mf_colorgroup.py output/xqcL_coin_P1S_AMS_colored.3mf
"""

import sys
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

NS_CORE = "http://schemas.microsoft.com/3dmanufacturing/core/2015/02"
NS_M = "http://schemas.microsoft.com/3dmanufacturing/material/2015/02"


def q(ns: str, tag: str) -> str:
    return f"{{{ns}}}{tag}"


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__.strip())
        return 2

    path = Path(sys.argv[1])
    if not path.exists():
        print(f"ERROR: file not found: {path}")
        return 2

    with zipfile.ZipFile(path, "r") as z:
        try:
            xml_bytes = z.read("3D/3dmodel.model")
        except KeyError:
            print("ERROR: 3MF missing 3D/3dmodel.model")
            return 1

    root = ET.fromstring(xml_bytes)

    # 3MF spec: requiredextensions is a space-separated list of *prefixes*.
    required = root.attrib.get("requiredextensions", "")
    required_tokens = required.split() if required else []
    has_required_ext = ("m" in required_tokens)

    # Also validate that xmlns:m maps to the expected material namespace.
    # ElementTree stores namespace declarations in tags, not attrs; easiest is to
    # just assert that we can find <m:colorgroup> using NS_M.

    resources = root.find(q(NS_CORE, "resources"))
    if resources is None:
        print("ERROR: missing <resources>")
        return 1

    colorgroups = resources.findall(q(NS_M, "colorgroup"))
    if not colorgroups:
        print("ERROR: no <m:colorgroup> found")
        return 1

    cg_ids = {cg.attrib.get("id") for cg in colorgroups}
    cg_ids.discard(None)

    colors_count = 0
    for cg in colorgroups:
        colors_count += len(cg.findall(q(NS_M, "color")))

    objects = resources.findall(q(NS_CORE, "object"))
    obj_with_mesh = 0
    tri_total = 0
    tri_missing = 0
    tri_bad_pid = 0
    tri_bad_p = 0

    for obj in objects:
        mesh = obj.find(q(NS_CORE, "mesh"))
        if mesh is None:
            continue
        obj_with_mesh += 1
        triangles = mesh.find(q(NS_CORE, "triangles"))
        if triangles is None:
            continue

        for tri in triangles.findall(q(NS_CORE, "triangle")):
            tri_total += 1
            pid = tri.attrib.get("pid")
            p1 = tri.attrib.get("p1")
            p2 = tri.attrib.get("p2")
            p3 = tri.attrib.get("p3")
            if pid is None or p1 is None or p2 is None or p3 is None:
                tri_missing += 1
                continue
            if pid not in cg_ids:
                tri_bad_pid += 1
            try:
                p1i, p2i, p3i = int(p1), int(p2), int(p3)
            except ValueError:
                tri_bad_p += 1
                continue
            if p1i < 0 or p2i < 0 or p3i < 0:
                tri_bad_p += 1

    build = root.find(q(NS_CORE, "build"))
    item_count = 0
    if build is not None:
        item_count = len(build.findall(q(NS_CORE, "item")))

    print(f"file: {path}")
    print(f"requiredextensions includes 'm': {has_required_ext} ({required!r})")
    print(f"colorgroups: {len(colorgroups)} (ids={sorted(cg_ids)}) colors_total={colors_count}")
    print(f"objects: {len(objects)} with_mesh={obj_with_mesh}")
    print(f"build items: {item_count}")
    print(f"triangles: {tri_total}")
    print(f"triangles missing pid/p1/p2/p3: {tri_missing}")
    print(f"triangles with pid not in colorgroup ids: {tri_bad_pid}")
    print(f"triangles with invalid p1/p2/p3: {tri_bad_p}")

    ok = (
        has_required_ext
        and colors_count > 0
        and tri_total > 0
        and tri_missing == 0
        and tri_bad_pid == 0
        and tri_bad_p == 0
        and item_count > 0
    )

    if not ok:
        print("FAIL")
        return 1

    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
