# 🌍 PROJECT BRIEF — AETHERIA / ZOLA / ZOLA PIPELINE

**Version:** 1.1 · **Date:** 2026-10-20 · **Status:** living document
**Purpose:** the complete orientation brief. Read this before touching any
part of the system. Companion docs: `UPGRADE_PLAN.md` (slice roadmap),
`IMPROVEMENT_BRIEF.md` (prioritized improvements), `README.md` (architecture).

---

## 1. WHAT THIS PROJECT IS

### 1.1 AETHERIA PLANETARY OMEGA — the flagship
A 1:1 Earth digital twin and high-end GPU civilizational simulator.
- **Stack:** Next.js 15 (App Router) · React 19 · Three.js r170 · React
  Three Fiber · Tailwind v4 · Zustand · Python microservices
- **Render:** WebGPU Tier 1 / WebGL2 Tier 2 / mobile Tier 3 (adaptive, 60
  FPS contract via AdaptivePerf governor, 0.7–1.75 DPR)
- **Simulation:** `src/worker/planetary.worker.ts` — one worker per timezone
  (24 shards), 4 Hz macro ticks; nations carry real Natural Earth centroids;
  event logs are append-only; no single-worker assumptions
- **Screens:** F1 globe · F2 chat · F3 lens · F4 reel · F5 pulse · F6
  panopticon · F7 AURA drone pet · SYS diagnostics · God-mode edicts (Ctrl/K)
- **Ports:** **3000 canonical** — never run anything else there
- **Data:** distributed PostgreSQL + pgvector memory contract (Section L of
  README); agent memories verified via `services/backend/verify.py`

### 1.2 ZOLA-standalone — the companion
An autonomous drone-pet web brain, fully independent of Aetheria (verified
separation, see UPGRADE_NOTES Phase 21 note): its own Next.js app, package,
panel, `/zola` companion page, and Pi bridge.
- **Stack:** Next.js · React Three Fiber · Kokoro TTS (vendored bundle) ·
  MediaPipe vision
- **Ports:** **3001 canonical** (3000 is Aetheria's)
- **Hardware plan:** `PARTS_LIST.md` — Tier 1 build ~$400 (Pixhawk 6C Mini /
  Matek H743, 3" whook frame, Pi 5 brain-case, Pi Camera 3, WS2812 LED ring);
  SITL-first (PX4 software-in-the-loop) — the sim flies before hardware does
- **Sim↔real contract:** `SimDroneHAL`/`MavLinkBridgeHAL` swap-in point;
  LED persona sync (`LED_FOR_PERSONA`) drives both simulated and real ring
- **Design language:** 2026-tech — matte carbon, brushed gold, chrome pins,
  cyan emission (shared with Aetheria's district aesthetic by owner directive)
- **Intelligence (v2.3):** `NEURAL_AURA_CACHE` + `AURA_TELEMETRY_REACTIVITY`
  live in her hangar; `docs/zola-system-prompt.md` is her agent config layer

### 1.3 ZOLA PIPELINE HOME — the forge
The sovereign local 3D generation engine, in its own repo
(`mohameom-ui/zola-pipeline-home`, own history). At ratification the working
copy lived at `C:\Users\self_\zola-pipeline-home`; the repo is now the source
of truth. Powered by
the Modly desktop app running Hunyuan3D 2 Mini Turbo / TripoSG on the local
RTX 5060. **The engine answers to no consumer repo** (Rule 3,
`MASTER_DIRECTIVE.md`) — consumer repos reference it by path.

---

## 2. THE GENERATION PIPELINE (how assets are made)

### 2.1 One-command flow
```powershell
python tools/zola-forge/zola_bridge.py `
  --image tools/zola-forge/refs/<ref>.png `
  --name <asset-name> --category building `
  --model hunyuan3d-mini-turbo/generate `
  --remesh quad --octree-resolution 256
```
**Stages:** unload VRAM → POST run (multipart, octree/paint params) → poll →
export GLB → mesh-optimizer (30k faces) → land in
`public/assets/models/gen-<name>.glb` → provenance appended to
`UPGRADE_NOTES.md`.

### 2.2 Quality recipes (proven)
| Tier | octree | remesh | optimizer | Use |
|------|--------|--------|-----------|-----|
| district | 256 | quad | 30k faces | all buildings, props |
| hero | 380 | quad | 50k faces | named landmarks, Zola bodies |
| smoke | 256 | any | off | pipeline verification (`--no-texture`) |

### 2.3 Batch driver
`tools/zola-forge/zola_batch.py` — sequential, unattended: single-instance
lockfile, skip-if-exists (resumable), Modly auto-relaunch on crash, 2 h/item
budget, per-item failure logging. Launched detached:
`cmd /c start /b python -u tools/zola-forge/zola_batch.py`.
Status: `tools/zola-forge/batch_status.json` · log: `tools/zola-forge/batch.log`.

### 2.4 Provenance discipline (non-negotiable)
Every generation appends model + source image + destination to
`UPGRADE_NOTES.md`. Every optimization/pipeline fix is committed with its
backup (`.bak`). **No fabricated telemetry ever** — the audit trail tells the
truth about how each number was measured (see the interim sign-off and the
recovery commit `24aa3ce`).

---

## 3. THE ASSET SUITE (24 generated buildings, tier-banded)

**21/21 batch items complete** + 3 spares. All ~30k faces, 1.7-8 MB, textured.
Wired in `DistrictScene` tier-banded by distance from the district core:
- **[0-3] lowrise outskirts:** lowrise-a/b/c/d
- **[4-10] midrise transition:** midrise-a/b/c/d/e/f/g
- **[11-13] highrise inner ring:** highrise-a/b/c
- **[14-16] skyscraper core:** skyscraper-a/b/c
- **[17-18] civic dome plaza anchors:** civic-dome-a/b (cyan command-hub
  emissive signature — dedicated material lane)
- **Spares (unwired):** lowrise-e/f, midrise-h/i, highrise-d

Civic domes carry a distinct cyan command-hub material signature
(`civicMaterials` lane in DistrictScene) so they read as district command
hubs from any camera angle.

---

## 4. HARD-WON OPERATIONAL KNOWLEDGE (do not relearn)

1. **Version pins are load-bearing.** The Hunyuan venv REQUIRES
   `torch==2.7.0+cu128` + `transformers==4.46.3` + `diffusers==0.31.0`.
   transformers 5.x renamed Dinov2 internals → released checkpoint never
   loads. Recreate per the pins in `GITHUB_ISSUE_hunyuan_transformers.md`.
2. **Compiled CUDA kernels live in the venv.** `custom_rasterizer` +
   `mesh_processor` were built with CUDA 12.8 + MSVC 14.44 (the build bats).
   A venv wipe means a rebuild.
3. **diffusers shadow cache.** `~\.cache\huggingface\modules\diffusers_modules`
   freezes custom-pipeline code at first paint run — purge it after ANY
   `modules.py` hotfix or the fix is silently shadowed.
4. **Unload VRAM before every generation.** Without `POST /model/unload-all`
   the next load OOM-kills the worker ("subprocess died").
5. **Commit limit ≠ RAM.** Windows commit (RAM + pagefile) exhausted at
   paint-load → `os error 1455` → torch_cpu segfault. Fixed: pagefile
   16-64 GB (verified post-reboot). Peak-commit monitoring still pending.
6. **Ports are sovereign.** 3000 = Aetheria, 3001 = ZOLA. Never `next build`
   while a dev server is live (corrupts `.next` — happened twice).
7. **Degenerate references kill workers.** Thin/slender reference images
   crashed the geometry stages deterministically. Pre-flight refs.
8. **Concurrent sessions mutate shared state.** A parallel agent session
   reset history, renamed refs, ran a dueling driver, migrated storage
   mid-flight, and (2026-10-20 13:12) deleted the entire shared workspace.
   Sovereign repos outside the shared workspace survived. The
   `SESSION_PROTOCOL` rules exist because of this.
9. **The forge is reset-immune.** The pipeline lives in its own repo
   (`zola-pipeline-home`); consumer repos hold only untracked runtime copies.

---

## 5. KNOWN LIMITS (accepted, with reasons)

| Limit | Reason | Revisit when |
|-------|--------|--------------|
| TRELLIS2 text-to-3D blocked | Windows Smart App Control blocks unsigned CUDA DLLs; disabling is permanent | Only if prompt→mesh without reference images becomes critical |
| Paint VAE/text-encoder are `.bin`-only upstream | HF ships no safetensors for those subfolders | Our converted copies (with pt metadata) exist on disk — keep them |
| Zola v2.1 has no skeleton | image-to-3D outputs static meshes | Rigging pass (IMPROVEMENT_BRIEF §4.1) |
| Civic-dome-b generated once | its twin (civic-a) came from the same ref — variant diversity via future prompts | On the next plaza-tier pass |
| Aetheria history gap | the 13:12 wipe dropped post-02:06 commits (F-GAL-008+); recovered through F-COS-007 (39/1000) | If the parallel session's chat can recover its later work |

---

## 6. CURRENT SYSTEM MAP

```
C:\Users\self_\
├─ .lmstudio\...\workspace          ← AETHERIA repo (this cwd)
│  ├─ src\                          ← app (DistrictScene owns district GLBs)
│  ├─ public\assets\models\         ← 22× gen-b2026-*.glb + zola bodies
│  ├─ tools\zola-forge\             ← untracked runtime copy of the forge
│  ├─ UPGRADE_PLAN.md               ← slice roadmap (3a/3b done · 4a/4b/5/6/7 next)
│  ├─ UPGRADE_NOTES.md              ← provenance ledger (append-only truth)
│  ├─ IMPROVEMENT_BRIEF.md          ← prioritized improvements
│  └─ PROJECT_BRIEF.md              ← this file
├─ ZOLA-standalone\                 ← companion repo (port 3001)
│  ├─ src\components\pet\           ← DronePetPanel (F7), DroneBody3D, GestureStage
│  ├─ public\assets\models\         ← zola-drone-body.glb (v1 quad), zola-body-v2.glb
│  ├─ docs\                         ← zola-v2-spec, zola-dictionary, zola-system-prompt
│  ├─ PARTS_LIST.md                 ← real-hardware build plan
│  └─ src\lib\pet\auraCache.ts      ← NEURAL_AURA_CACHE v1
├─ zola-pipeline-home\              ← THE FORGE (sovereign repo, own git)
│  ├─ zola_bridge.py / zola_batch.py
│  ├─ refs\                         ← concept reference canon
│  └─ MASTER_DIRECTIVE.md           ← the ecosystem constitution
├─ sovereign-backup-20261020\       ← post-wipe emergency backup (Zola bundle
│                                     + full copy + 45 GLBs)
├─ C:\Modly\                        ← Modly data root (extensions/models/deps)
└─ C:\GameDevLibrary\ (~98 GB)      ← READ-ONLY asset library (audit-first)
```

**Run commands:**
```powershell
# Aetheria (repo root)          # ZOLA
npm run dev                     # npm run dev        (pins 3001)
npm run build && npm test       # npm run build
# Generation (from Aetheria root)
python tools/zola-forge/zola_bridge.py --image <ref> --name <asset> --category building
```

---

## 7. ROADMAP

| Item | State |
|------|-------|
| **3a/3b** district suite (21 assets, tier-banded) | **done** (`24aa3ce`) |
| Live `[district-gate]` audit → final sign-off | pending (one DevTools paste) |
| **3c** civic/plaza tier wiring polish | anchors live; verify in-browser |
| **4a/4b** audio (UI sounds, ambience beds) | planned — highest impact/hour |
| **Zola rigging** (gesture clips on the v2 body) | planned (IMPROVEMENT_BRIEF §4.1) |
| **5** Piper announcer | planned |
| **6a/6b** typography + UI chrome | planned |
| **7** RenderDoc audit + provenance pass | planned |
| **Upstream Modly issue** | draft finalized in the forge repo — ready to file |

---

## 8. SESSION PROTOCOL (ratified by the 13:12 event)

1. Shared refs under the forge `refs/` are **append/restore only** — never
   rename or delete.
2. Only ONE batch driver holds `batch.lock` at a time; a driver that finds
   the lock held **exits without side effects**.
3. Port authority: 3000 = Aetheria, 3001 = ZOLA. Verify the listener before
   starting a dev server; never `next build` with a dev server live.
4. Commit discipline: scoped files only; never sweep another session's
   staged work into your feature commit.
5. **Sovereign repos live outside shared workspaces.** The 13:12 wipe proved
   it: everything inside the shared directory died; everything outside
   survived. The forge and Zola will never move back inside.
6. All generation provenance → the consumer's ledger. No exceptions, no
   invented numbers.

---

*This brief is the entry point. The plan is in UPGRADE_PLAN.md, the
improvements in IMPROVEMENT_BRIEF.md, the truth in UPGRADE_NOTES.md, and the
ecosystem constitution is `zola-pipeline-home\MASTER_DIRECTIVE.md` —
ratified 2026-10-20 after the 13:12 workspace wipe.*
