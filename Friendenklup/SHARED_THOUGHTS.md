# SHARED_THOUGHTS

## Current Objective
- Maintain guild-routed project workspace for Friendenklup.
- Create and publish a 3D-printable STL for the xqcL emoji.

## Architecture Snapshot
- Root: /home/server/openclaw-projects/Friendenklup

## Decisions
- Guild 695349915169062968 is pinned to this root.
- For Bambu Studio multi-color import, encode colors via 3MF **colorgroup** + **triangle-level** `pid/p1/p2/p3` (do not rely on object-level `pid/pindex`).
- Emit two 3MF build layouts (separate build items + components assembly) to handle slicer/importer differences.

## Failed Attempts
- none

## Open Questions
- none

## Next Steps
- Fix Bambu Studio color import for xqcL_coin_P1S_AMS*.3mf (current file imports as geometry-only / single material).
  - Suspect: project-less 3MF + incorrect/insufficient 3MF color encoding (needs triangle-level pid+p1/p2/p3 and/or requiredextensions; possibly assembly/components handling).
- Rebuild and publish a verified P1S+AMS-ready 3MF that opens with multiple colors/parts in Bambu Studio.
