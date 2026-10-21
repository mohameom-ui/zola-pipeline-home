import json, time, urllib.request, urllib.parse, shutil, sys
from pathlib import Path
API = "http://127.0.0.1:8765"
RUN = "1a18b6ab-51a7-4672-b7d8-c283cd029657"
DEST = Path("C:/Users/self_/ZOLA-standalone/public/assets/models/gen-zola-v3-34view.glb")
deadline = time.time() + 7200
while time.time() < deadline:
    try:
        with urllib.request.urlopen(f"{API}/workflow-runs/{RUN}", timeout=30) as r:
            last = json.loads(r.read().decode())
    except Exception as e:
        print(f"[poll] transient: {e}", flush=True); time.sleep(15); continue
    st = last.get("status")
    print(f"[poll] {st}", flush=True)
    if st == "error":
        print("FAILED:", str(last.get("error"))[:1000], flush=True); sys.exit(1)
    if st == "done":
        out = str(last.get("output_url") or "")
        ws_rel = out[len("/workspace/"):] if out.startswith("/workspace/") else out
        print("output:", ws_rel, flush=True)
        with urllib.request.urlopen(f"{API}/export/glb?path={urllib.parse.quote(ws_rel)}", timeout=600) as r, DEST.open("wb") as fh:
            shutil.copyfileobj(r, fh)
        print(f"LANDED: {DEST} ({DEST.stat().st_size} bytes)", flush=True)
        wp = last.get("workspace_path")
        if wp:
            try:
                with urllib.request.urlopen(f"{API}/optimize/mesh?{urllib.parse.urlencode({'path': wp, 'target_faces': 30000})}", timeout=600) as r:
                    opt = json.loads(r.read().decode())
                cand = opt.get("path") or opt.get("output_path")
                if cand:
                    with urllib.request.urlopen(f"{API}/optimize/export?{urllib.parse.urlencode({'path': cand, 'fmt': 'glb'})}", timeout=600) as r, DEST.open("wb") as fh:
                        shutil.copyfileobj(r, fh)
                    print(f"OPTIMIZED: {DEST.stat().st_size} bytes", flush=True)
            except Exception as e:
                print(f"[optimize] best-effort skipped: {e}", flush=True)
        sys.exit(0)
    time.sleep(20)
print("TIMED OUT", flush=True); sys.exit(1)
