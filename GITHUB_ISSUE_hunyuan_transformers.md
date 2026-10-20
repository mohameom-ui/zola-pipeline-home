# Hunyuan3D Mini Turbo extension broken on fresh installs: transformers 5.x renames Dinov2 params, released checkpoint never loads

**Environment:** Modly 0.4.3 (Windows installer), RTX 5060 Laptop, Windows 11, extension `lightningpixel/modly-hunyuan3d-mini-turbo-extension` v1.0.0 installed 2026-10-19.

## Summary

On a fresh extension install, mesh generation fails in `Hunyuan3DDiTFlowMatchingPipeline.from_pretrained` with:

```
RuntimeError: Error(s) in loading state_dict for SingleImageEncoder:
    Missing key(s):   main_image_encoder.model.encoder.layer.N.attention.{q,k,v,o}_proj.*, mlp.{gate,up,down}_proj.*
    Unexpected key(s): main_image_encoder.model.encoder.layer.N.attention.attention.{query,key,value}.*, attention.output.dense.*, mlp.weights_in/weights_out.*
```

## Root cause

1. The extension's `setup.py` declares `transformers>=4.46.0` — an **open-ended floor**. pip resolves it to **transformers 5.x** on a fresh install.
2. transformers 5.x refactored `Dinov2Model` internals: attention now exposes `q_proj/k_proj/v_proj/o_proj` (the old `attention.attention.{query,key,value}` submodule names are gone) and the MLP became a gated MLP (`gate_proj/up_proj/down_proj` instead of `weights_in/weights_out`).
3. The released turbo checkpoint (`hunyuan3d-dit-v2-mini-turbo/model.fp16.safetensors`) stores conditioner weights in the **old 4.x naming**, verified by reading the safetensors header:
   - checkpoint: `conditioner.main_image_encoder.model.encoder.layer.0.attention.attention.query.weight` …
   - model expects: `main_image_encoder.model.encoder.layer.0.attention.q_proj.weight` …
4. hy3dgen loads the conditioner via a raw `conditioner.load_state_dict(ckpt['conditioner'])` (bypassing transformers' legacy-key remapping), so the mismatch is fatal.

**Fix that worked for us:** pin the extension venv to era-consistent versions:

```
pip install torch==2.7.0+cu128 torchvision==0.22.0+cu128 --index-url https://download.pytorch.org/whl/cu128
pip install transformers==4.46.3 diffusers==0.31.0
```

(the transformers downgrade also downgrades `huggingface_hub` below what current `diffusers` needs — `diffusers` must be pinned to a matching ~0.31 as well, otherwise `cannot import name 'resolve_revision' from 'huggingface_hub'`)

## Additional install-time issues encountered on the same machine

1. **Partial-torch import race during first `load()`**: `_ensure_hy3dgen()`'s dependency resolution upgraded torch *while* the worker process was importing it, leaving a poisoned partial `torch` module in the long-lived extension process. Subsequent runs kept failing until `/model/unload-all` recycled the worker. Consider installing hy3dgen deps before first load, or importing in a fresh process after setup.
2. **Missing runtime deps at texture stage** (first textured generation): `xatlas`, `pygltflib`, and for manual extension builds `wheel` + `pybind11`. Adding them to the extension's `requirements`/`setup.py` would save users several failed runs.
3. **`setup.py install` (egg) fails on OneDrive-synced workspaces**: egg extraction hit `WinError 5 Access denied` mid-copy while OneDrive held locks. `pip install .` (wheel path) works.

## Additional runtime issue (4): diffusers custom-module shadow cache

4. **Stale custom-pipeline cache hides code fixes** — after the first successful textured run, diffusers copies the custom pipeline's `unet/modules.py` (from the *checkpoint* folder, not the patched `_hy3dgen` source) into `~\.cache\huggingface\modules\diffusers_modules\local\` and keeps importing that frozen copy. Any hotfix to the loader is silently shadowed by the cache on subsequent runs. Deleting `diffusers_modules/local` restores correctness. Worth either documenting or version-stamping the cache per extension.

## Suggested fixes

- Pin `transformers` to `>=4.46,<5` (or whatever range keeps the released checkpoint's Dinov2 naming), and pin `diffusers`/`huggingface_hub` to a mutually compatible set in the extension `setup.py`.
- Declare the full transitive dep set used at texture time (`xatlas`, `pygltflib`) up front.
- Prefer wheel-based installs over eggs for venvs on cloud-synced paths.
