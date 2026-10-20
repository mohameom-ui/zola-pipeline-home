#!/usr/bin/env python3
"""Batch 2026-tech building restyle driver (slice 3a).

Generates the remaining district buildings via tools/modly/aetheria_bridge.py
(generate -> paint -> mesh-optimizer -> export), sequentially, unattended.

- Logs to tools/modly/batch.log
- Writes live status to tools/modly/batch_status.json
- If the Modly app dies mid-batch, relaunches it and waits for the backend
  (it crashed once between long bakes).

Run detached:
    cmd /c start /b python tools/modly/batch_generate.py
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
BRIDGE = HERE / "aetheria_bridge.py"
LOG = HERE / "batch.log"
STATUS = HERE / "batch_status.json"
MODLY_EXE = Path(r"C:\Users\self_\AppData\Local\Programs\Modly\Modly.exe")

# (asset name, reference image, prompt note)
PLAN = [
    ("b2026-midrise-b",    "refs/ref-2026-midrise-b.png",    "white terraced mid-rise, solar canopy, gold mast"),
    ("b2026-lowrise-a",    "refs/ref-2026-lowrise.png",      "low podium: glass retail, gold band, rooftop garden, LED crown"),
    ("b2026-highrise-b",   "refs/ref-2026-highrise.png",     "carbon tower, vertical LED fins, holo panels"),
    ("b2026-midrise-c",    "refs/ref-2026-midrise-a.png",    "dark glass + gold trim + sky-gardens (variant)"),
    ("b2026-lowrise-b",    "refs/ref-2026-lowrise.png",      "low podium variant"),
    ("b2026-midrise-d",    "refs/ref-2026-midrise-b.png",    "white terraces variant"),
    ("b2026-highrise-c",   "refs/ref-2026-highrise.png",     "carbon tower variant"),
    ("b2026-midrise-e",    "refs/ref-2026-midrise-a.png",    "dark glass + gold variant"),
    ("b2026-lowrise-c",    "refs/ref-2026-lowrise.png",      "low podium variant"),
    ("b2026-midrise-f",    "refs/ref-2026-midrise-b.png",    "white terraces variant"),
    ("b2026-midrise-g",    "refs/ref-2026-midrise-a.png",    "dark glass variant"),
    ("b2026-lowrise-d",    "refs/ref-2026-lowrise.png",      "low podium variant"),
    ("b2026-skyscraper-b", "refs/ref-2026-skyscraper-a.png", "tapered setbacks + cyan beacon variant"),
    ("b2026-skyscraper-c", "refs/ref-2026-skyscraper-b.png", "slender spire + holo rings + gold beacon"),
]

MODLY_API = "http://127.0.0.1:8765"


def log(msg: str) -> None:
    line = f"[{datetime.now().strftime('%H:%M:%S')}] {msg}"
    print(line, flush=True)
    with LOG.open("a", encoding="utf-8") as fh:
        fh.write(line + "\n")


def write_status(done: list[str], failed: list[str], current: str) -> None:
    STATUS.write_text(json.dumps({
        "updated": datetime.now().isoformat(timespec="seconds"),
        "done": done, "failed": failed, "current": current,
        "total": len(PLAN),
    }, indent=2), encoding="utf-8")


def ensure_modly() -> bool:
    import urllib.request
    try:
        with urllib.request.urlopen(f"{MODLY_API}/health", timeout=5):
            return True
    except Exception:
        pass
    if MODLY_EXE.exists():
        log("Modly down — relaunching…")
        subprocess.Popen(["cmd", "/c", "start", "", str(MODLY_EXE)],
                         creationflags=subprocess.CREATE_NO_WINDOW)
        for _ in range(18):
            time.sleep(10)
            try:
                with urllib.request.urlopen(f"{MODLY_API}/health", timeout=5):
                    log("Modly backend back up.")
                    return True
            except Exception:
                continue
    return False


LOCK = HERE / "batch.lock"

def acquire_lock() -> bool:
    """Single-instance guard: atomic O_EXCL create; steal stale locks (>3h)."""
    try:
        if LOCK.exists():
            age = time.time() - LOCK.stat().st_mtime
            if age < 3 * 3600:
                return False
            LOCK.unlink()
        fd = os.open(str(LOCK), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.write(fd, str(os.getpid()).encode())
        os.close(fd)
        return True
    except FileExistsError:
        return False

def main() -> int:
    if not acquire_lock():
        print("another batch driver holds the lock — exiting", flush=True)
        return 0
    done: list[str] = []
    failed: list[str] = []
    for i, (name, ref, note) in enumerate(PLAN):
        write_status(done, failed, name)
        log(f"=== [{i+1}/{len(PLAN)}] {name} ===")
        if not ensure_modly():
            log(f"SKIP {name}: Modly unavailable")
            failed.append(name)
            continue
        out_path = HERE.parent.parent / "public" / "assets" / "models" / f"gen-{name}.glb"
        if out_path.exists():
            done.append(name)
            log(f"SKIP {name}: already generated")
            continue
        cmd = [
            sys.executable, str(BRIDGE),
            "--image", str(HERE / ref),
            "--name", name,
            "--category", "building",
            "--model", "hunyuan3d-mini-turbo/generate",
            "--remesh", "quad",
            "--octree-resolution", "256",
            "--prompt", f"2026-tech architecture: {note}",
        ]
        env = dict(os.environ, MODLY_CLI_TIMEOUT="7200")
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", timeout=7200, env=env)
        tail = (r.stdout or "") + (r.stderr or "")
        if '"ok": true' in tail:
            done.append(name)
            log(f"DONE {name}")
        else:
            failed.append(name)
            log(f"FAIL {name}: {tail[-400:]}")
    write_status(done, failed, "")
    log(f"=== BATCH COMPLETE: {len(done)} ok, {len(failed)} failed ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
