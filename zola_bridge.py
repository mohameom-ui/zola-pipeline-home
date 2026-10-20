#!/usr/bin/env python3
"""Aetheria <- Modly generation bridge.

Wraps the stdlib-only Modly agent CLI (agent.py, vendored from
lightningpixel/modly, MIT) to generate textured meshes with the local Modly
desktop app and land them directly in Aetheria's asset tree.

Usage:
    python tools/modly/aetheria_bridge.py --image refs/tower.png \
        --name gen-tower-sandstone --category building

    python tools/modly/aetheria_bridge.py health
    python tools/modly/aetheria_bridge.py models

Prerequisites:
    - Modly desktop app running (v0.4.3+), FastAPI backend reachable at
      http://127.0.0.1:8765 (override with MODLY_API_URL).
    - At least one model extension installed with weights downloaded
      (Hunyuan3D 2 Mini Turbo recommended for 8 GB laptop GPUs).

Pipeline per asset: generate -> paint (hy3dgen) -> Modly mesh-optimizer
(decimate to --target-faces, default 30000) -> export GLB into
public/assets/models/. Every successful generation appends a provenance
entry to UPGRADE_NOTES.md per the project's verification gates.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.request
import urllib.parse
import time as _time
import uuid as _uuid
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
AGENT = Path(__file__).resolve().parent / "agent.py"
MODELS_DIR = REPO_ROOT / "public" / "assets" / "models"
NOTES = REPO_ROOT / "UPGRADE_NOTES.md"
API_BASE = os.environ.get("MODLY_API_URL", "http://127.0.0.1:8765")

# Generated assets get the `gen-` prefix so they never collide with
# library-sourced kit names (building-a.glb, tree_default.glb, ...).
NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
CATEGORIES = ("building", "nature", "landmark", "prop", "scene")


def run_agent(args: list[str], *, quiet: bool = False) -> dict:
    """Run agent.py and return its final JSON object."""
    proc = subprocess.run(
        [sys.executable, str(AGENT), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=7200,
    )
    if not quiet:
        if proc.stderr:
            print(proc.stderr, file=sys.stderr, end="")
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError:
        if proc.returncode != 0:
            raise SystemExit(
                f"agent.py failed (exit {proc.returncode}):\n{proc.stdout[-2000:]}"
            )
        raise SystemExit(f"agent.py returned non-JSON output:\n{proc.stdout[-2000:]}")


def _post_generation_run(image_path: Path, model_id: str, params: dict) -> str:
    """POST /workflow-runs/from-image directly (agent.py can't pass generator
    params like octree_resolution). Returns the run id."""
    boundary = f"----aetheria-{_uuid.uuid4().hex}"
    fields = {
        "model_id": model_id,
        "collection": "Agent",
        "params": json.dumps(params),
    }
    body = b""
    for k, v in fields.items():
        body += f"--{boundary}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n{v}\r\n".encode()
    mime = "image/png" if image_path.suffix.lower() == ".png" else (
        "image/jpeg" if image_path.suffix.lower() in (".jpg", ".jpeg") else "image/webp")
    body += (
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"image\"; filename=\"{image_path.name}\"\r\n"
        f"Content-Type: {mime}\r\n\r\n"
    ).encode() + image_path.read_bytes() + f"\r\n--{boundary}--\r\n".encode()
    req = urllib.request.Request(
        f"{API_BASE}/workflow-runs/from-image",
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read().decode())["run_id"]


def _poll_generation_run(run_id: str, timeout_s: float) -> dict:
    deadline = _time.time() + timeout_s
    last = {}
    while _time.time() < deadline:
        try:
            with urllib.request.urlopen(f"{API_BASE}/workflow-runs/{run_id}", timeout=30) as resp:
                last = json.loads(resp.read().decode())
        except Exception as exc:
            print(f"[poll] transient error: {exc}", file=sys.stderr)
            _time.sleep(15)
            continue
        status = last.get("status")
        if status == "done":
            return last
        if status == "error":
            raise SystemExit(f"Generation run failed: {str(last.get('error'))[:1500]}")
        _time.sleep(5)
    raise SystemExit(f"Generation run timed out after {int(timeout_s)}s: {json.dumps(last)[:500]}")


def _export_ws_mesh(ws_rel: str, fmt: str, dest: Path) -> None:
    url = f"{API_BASE}/export/{fmt}?{urllib.parse.urlencode({'path': ws_rel})}"
    with urllib.request.urlopen(url, timeout=600) as resp, dest.open("wb") as fh:
        shutil.copyfileobj(resp, fh)


def _modly_workspace_dir() -> Path | None:
    try:
        settings = json.loads(
            (Path(os.environ.get("APPDATA", "")) / "Modly" / "settings.json").read_text(encoding="utf-8")
        )
        return Path(settings["workspaceDir"])
    except Exception:
        return None


def _optimize_mesh(ws_rel: str, target_faces: int) -> Path | None:
    """Decimate the workspace mesh via Modly's optimizer; return local path."""
    req = urllib.request.Request(
        f"{API_BASE}/optimize/mesh",
        data=json.dumps({"path": ws_rel, "target_faces": int(target_faces)}).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=900) as resp:
        opt = json.loads(resp.read().decode())
    opt_path = opt.get("path") or opt.get("url") or (opt.get("payload") or {}).get("path")
    if not opt_path:
        return None
    opt_path = str(opt_path)
    if opt_path.startswith("/workspace/"):
        opt_path = opt_path[len("/workspace/"):]
    cand = Path(opt_path)
    if not cand.is_absolute():
        ws = _modly_workspace_dir()
        if ws is None:
            return None
        cand = ws / opt_path
    return cand if cand.exists() else None


def append_provenance(name: str, category: str, source: str, model: str, path: Path) -> None:
    stamp = _dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    entry = (
        f"\n### {stamp} — Modly generation: `{path.name}`\n"
        f"- **Tool:** Modly (local, lightningpixel/modly) via `tools/modly/aetheria_bridge.py`\n"
        f"- **Model:** {model or 'active'}\n"
        f"- **Source:** {source}\n"
        f"- **Category:** {category}\n"
        f"- **Destination:** `public/assets/models/{path.name}`\n"
    )
    with NOTES.open("a", encoding="utf-8") as fh:
        fh.write(entry)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--image", help="Reference image path (photograph or render) for image-to-3D")
    p.add_argument("--prompt", help="Prompt text recorded in provenance (and future text-to-3D paths)")
    p.add_argument("--name", required=True, help="Asset name, e.g. gen-tower-sandstone (gen- prefix enforced)")
    p.add_argument("--category", default="prop", choices=CATEGORIES)
    p.add_argument("--model", default="auto", help="Modly model id, 'active', or 'auto'")
    p.add_argument("--format", default="glb", choices=("glb", "obj", "stl", "ply"))
    p.add_argument("--remesh", default="quad", choices=("quad", "triangle", "none"))
    p.add_argument("--no-texture", action="store_true", help="Geometry-only, faster smoke tests")
    p.add_argument("--no-optimize", action="store_true", help="Skip Modly mesh-optimizer decimation")
    p.add_argument("--target-faces", type=int, default=30000, help="Optimizer face target (default 30000)")
    p.add_argument("--octree-resolution", type=int, default=380, help="Generator octree resolution: 256=Low/fast, 380=High (default 380)")
    args = p.parse_args()

    name = args.name if args.name.startswith("gen-") else f"gen-{args.name}"
    if not NAME_RE.match(name):
        raise SystemExit(f"Invalid asset name: {name!r} (use lowercase letters, digits, hyphens)")

    if args.image is None:
        p.error("--image is required (text-to-3D lands via workflow runs; see README)")

    # 1. Health check — fail fast with a human-readable message.
    health = run_agent(["health"], quiet=True)
    if not health.get("ok", health.get("healthy", True)):
        raise SystemExit(f"Modly API not healthy: {json.dumps(health)}")

    # 1b. Free VRAM from any previously loaded models — on an 8 GB card the
    # resident shape+paint models OOM the next load if not unloaded first.
    try:
        req = urllib.request.Request(f"{API_BASE}/model/unload-all", method="POST")
        urllib.request.urlopen(req, timeout=120).read()
        print("[vram] unloaded resident models", file=sys.stderr)
    except Exception as exc:
        print(f"[vram] unload skipped ({exc})", file=sys.stderr)

    # 2. Generate into a temp dir, then export to the requested format.
    with tempfile.TemporaryDirectory(prefix="aetheria-modly-") as tmp:
        out = Path(tmp) / f"out.{args.format}"
        params = {
            "remesh": args.remesh,
            "enable_texture": not args.no_texture,
            "texture_resolution": 1024,
            "octree_resolution": int(args.octree_resolution),
        }
        run_id = _post_generation_run(Path(args.image).resolve(), args.model, params)
        print(f"[run] {run_id} (octree={args.octree_resolution})", file=sys.stderr)
        result = _poll_generation_run(run_id, timeout_s=7200)
        out_url = str(result.get("output_url") or "")
        ws_rel = out_url[len("/workspace/"):] if out_url.startswith("/workspace/") else out_url
        if not ws_rel:
            raise SystemExit(f"Run finished without output: {json.dumps(result)[:500]}")
        _export_ws_mesh(ws_rel, args.format, out)

        # 2b. Mesh optimization (default): decimate via Modly's optimizer so
        # district-scale payloads stay light. Runs on the workspace copy.
        final_src = out
        ws_rel = result.get("workspace_path")
        if ws_rel and not args.no_optimize:
            try:
                cand = _optimize_mesh(ws_rel, args.target_faces)
                if cand:
                    final_src = cand
                    print(f"[optimize] decimated -> {cand.name}", file=sys.stderr)
            except Exception as exc:  # optimizer is best-effort; raw mesh still ships
                print(f"[optimize] skipped ({exc})", file=sys.stderr)

        # 3. Land the mesh in Aetheria's asset tree.
        MODELS_DIR.mkdir(parents=True, exist_ok=True)
        dest = MODELS_DIR / f"{name}.{args.format}"
        shutil.copy2(final_src, dest)

    model_id = str(result.get("model") or args.model)
    source = f"prompt: {args.prompt!r}" if args.prompt else ""
    if args.image:
        source = f"image: {args.image}" + (f" ({source})" if source else "")
    append_provenance(name, args.category, source, model_id, dest)

    print(json.dumps({"ok": True, "asset": str(dest.relative_to(REPO_ROOT)), "model": model_id}, indent=2))


if __name__ == "__main__":
    main()
