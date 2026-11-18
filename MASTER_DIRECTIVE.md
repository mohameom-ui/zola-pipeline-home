# 📜 MASTER DIRECTIVE — HOUSE ZOLA (ratified constitution)

**Ratified:** 2026-10-20 (owner directive). The constitution for the
three-sovereign ecosystem: this forge · Aetheria (3000) · ZOLA (3001).

## 1. SOVEREIGN ARCHITECTURE & REPOSITORY BOUNDARIES

```
┌────────────────────────────────────────────────────────────────────────┐
│                     zola-pipeline-home (THE FORGE)                     │
│       • Standalone 3D generation & optimization engine                 │
│       • Local pipeline (Hunyuan3D / CUDA / remesh / texture bake)     │
│       • Exports raw GLB binaries — zero UI runtime logic               │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
           ┌────────────────────────┴────────────────────────┐
           ▼                                                 ▼
┌──────────────────────────┐                      ┌──────────────────────────┐
│         AETHERIA         │                      │           ZOLA           │
│      (localhost:3000)    │                      │      (localhost:3001)    │
│  • Digital Twin City     │                      │  • Sovereign AI Drone Pet│
│  • Independent Renderer  │                      │  • Autonomous Hangar UI  │
│  • Static asset consumer │                      │  • Optic-Rizz Recon HUD  │
└──────────────────────────┘                      └──────────────────────────┘
```

- **Rule 1 (Zero Cross-Contamination):** Zola does **NOT** exist inside
  Aetheria. She is not an NPC, pedestrian, or embedded module on port 3000.
  She resides exclusively on port 3001 (`localhost:3001/zola`).
- **Rule 2 (Absolute Provenance):** No fake telemetry, no simulated test
  numbers, no fabricated benchmark outputs. All records must reflect true
  client-side DevTools evaluations or true pipeline hardware runs.
- **Rule 3 (Engine Sovereignty):** the generation engine lives HERE, in its
  own repo with its own history. Consumer repos reference it by path.
  No consumer may reset, quarantine, or rewrite the engine's history.

## 2. ZOLA v2.2 — SOVEREIGN AI DRONE PET SPECIFICATION

> **Status note (2026-11-18):** this section is the ratified 2026-10-20
> baseline and is kept as written. The current body is v13.0.0 — 1759 mm
> biped, 41 joints, four ducted collar fans at the neck base — specified in
> the ZOLA repo's `docs/ZOLA-KNOWLEDGE-BASE.md`. Where the two disagree, the
> knowledge base wins on hardware; this directive still governs repository
> boundaries and provenance.

Full system prompt: ZOLA repo `docs/zola-system-prompt.md`.
Lexicon: ZOLA repo `docs/zola-dictionary.md`.

- **Entity Type:** Independent Bipedal-Multirotor AI Drone Pet & Technical
  Recon Companion.
- **Home Base:** Hangar Port 3001 (`localhost:3001/zola`).
- **Hardware Profile:** Quad-Halo (12 cm × 12 cm carbon frame, four
  micro-brushless motors) · Tattu Ballast Bay (3S LiPo, low-CG) ·
  MG90S Servo Nodes · UART Trace Wire Mapping.
- **Subsystems:** `Optic-Rizz Array` · `HUD_TARGET_ID` ·
  `Uncertainty-Gaze` & `FALLBACK_RECON_SEARCH` · `NEURAL_AURA_CACHE` ·
  `Aura-Telemetry`.
- **Personality:** terminally online, witty, hyper-competent,
  unapologetically sassy.
- **Retracted:** `DISTRICT_PATROL_PATHFINDING` — prohibited. Zola operates
  100% within her own viewport and Hangar on port 3001.

## 3. FORGE STATUS & BATCH TRACKING

- **This repo:** independent git (init `dd7d991`).
- **Batch lineage:** Slice 3a (17 assets) + Slice 3b (7 assets, civic domes
  included) = **24 generated assets** delivered across both consumers.
- **Aetheria runtime copy:** `tools/zola-forge/` (untracked, quarantined —
  the forge answers to no consumer repo; sync flows forge → consumer).

## 4. PROVENANCE
Consumer ledgers: Aetheria `UPGRADE_NOTES.md` · ZOLA
`ZOLA_UPGRADE_NOTES.md`. This repo tracks the engine.
