# [Bug] `texture_resolution` generator param is silently ignored on /workflow-runs/from-image

## Environment
- Modly desktop v0.4.3+, FastAPI backend `127.0.0.1:8765`
- Extension: `hunyuan3d-mini-turbo` (pinned: torch 2.7.0+cu128, transformers 4.46.3, diffusers 0.31.0)
- Caller: external bridge POSTing multipart to `/workflow-runs/from-image`

## Steps to reproduce
1. POST `/workflow-runs/from-image` with `params = {"remesh":"quad","enable_texture":true,"texture_resolution":2048,"octree_resolution":256}`
2. Wait for the run to complete (`status: done`)
3. Export the result GLB

## Observed
- Two runs with identical image + octree, differing only in `texture_resolution` (1024 vs 2048)
  produce GLBs that are **byte-identical in size within 28 bytes** and render identically —
  the 2048 bake is not applied.

## Expected
- `texture_resolution` should drive the texture paint resolution (or the API should reject
  unknown/unsupported params with a 4xx naming the field, instead of silently accepting them).

## Related finding
- Multipart POSTs from our bridge initially failed with `400 Bad Request` while an
  equivalent curl-built multipart succeeded — worth auditing the endpoint's form parsing
  for strictness with header casing/boundary formats.

## Impact
- External automation (batch asset pipelines) cannot raise texture quality; meshes with
  130k+ vertices end up textured at 1024px, which reads blurry at any reasonable camera
  distance.

Happy to provide the two GLBs and the exact request bodies if useful.
