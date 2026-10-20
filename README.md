# 🐝 ZOLA PIPELINE HOME — the forge of House Zola

**The sovereign generation engine.** Powered by the [Modly](https://github.com/lightningpixel/modly)
desktop app (MIT, Lightning Pixel) running open-source image-to-3D models
(Hunyuan3D 2 Mini Turbo, TripoSG) entirely on the local RTX 5060.

**Ratified home of House Zola** per the MASTER_DIRECTIVE (2026-10-20) —
extracted from the Aetheria workspace after the parallel session's history
reset and the 13:12 workspace wipe. The engine answers to no consumer repo.

## Contents
- `zola_bridge.py` — the one-command asset pipeline: unload VRAM →
  workflow run → poll → export → mesh-optimizer (30k faces) → land GLB →
  provenance ledger entry
- `zola_batch.py` — resumable unattended batch driver: single-instance
  lockfile, skip-if-exists, Modly auto-relaunch, 2 h/item budget
- `agent.py` — vendored Modly agent CLI (MIT, lightningpixel/modly)
- `build_texgen.bat` / `build_renderer.bat` — CUDA 12.8 + MSVC 14.44 kernel
  build recipe (custom_rasterizer + mesh_processor)
- `GITHUB_ISSUE_hunyuan_transformers.md` — upstream issue draft (ready to file)
- `refs/` — concept reference canon (append-only)
- `MASTER_DIRECTIVE.md` — the ecosystem constitution

## Runtime contract
Modly desktop app running (FastAPI at 127.0.0.1:8765). Hunyuan venv pins:
`torch==2.7.0+cu128` · `transformers==4.46.3` · `diffusers==0.31.0`.
Compiled CUDA kernels required for texture paint (see the build bats).
Pagefile ≥ 16-64 GB (os error 1455 — commit-limit exhaustion).

## Consumers (by path, zero coupling)
- **Aetheria** (Port 3000) — consumes exported GLBs into
  `public/assets/models/` (its runtime copy of the bridge lives in
  `tools/zola-forge/`, untracked)
- **ZOLA** (Port 3001) — her bodies, her spec assets; the Optic-Rizz Array
  scans what enters her viewport

## Provenance
All asset generations append to the consumer's ledger
(Aetheria: `UPGRADE_NOTES.md` · ZOLA: `ZOLA_UPGRADE_NOTES.md`).
This repo tracks the engine itself.
