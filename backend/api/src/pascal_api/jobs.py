"""Background jobs (thread pool) with JSON status files, so a restart keeps the history. A job function gets `log(msg)` and returns a JSON-able dict."""
import json
import threading
import time
import traceback
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path


class JobStore:
    def __init__(self, data_dir: Path, workers: int = 2):
        self.dir = Path(data_dir) / "jobs"
        self.dir.mkdir(parents=True, exist_ok=True)
        self.pool = ThreadPoolExecutor(max_workers=workers, thread_name_prefix="pascal-job")
        self.lock = threading.Lock()
        self.jobs = {}
        for p in self.dir.glob("*.json"):
            try:
                j = json.loads(p.read_text(encoding="utf-8"))
                if j.get("status") in ("queued", "running"):
                    j["status"], j["error"] = "failed", "service restarted while the job was running"
                    p.write_text(json.dumps(j, indent=1), encoding="utf-8")
                self.jobs[j["id"]] = j
            except Exception:
                pass

    def _save(self, j):
        (self.dir / f"{j['id']}.json").write_text(json.dumps(j, indent=1, ensure_ascii=False, default=str), encoding="utf-8")

    def submit(self, kind: str, project: str, fn) -> dict:
        j = {"id": uuid.uuid4().hex[:12], "kind": kind, "project": project, "status": "queued", "created": time.strftime("%Y-%m-%dT%H:%M:%S"),
             "started": None, "finished": None, "log": [], "result": None, "error": None}
        with self.lock:
            self.jobs[j["id"]] = j
            self._save(j)

        def run():
            def log(msg):
                with self.lock:
                    j["log"].append(time.strftime("%H:%M:%S") + " " + str(msg))
                    self._save(j)
            with self.lock:
                j["status"], j["started"] = "running", time.strftime("%Y-%m-%dT%H:%M:%S")
                self._save(j)
            try:
                res = fn(log)
                with self.lock:
                    j["status"], j["result"] = "succeeded", json.loads(json.dumps(res, default=str))
            except Exception as e:  # a job never kills the pool; the error is the result
                with self.lock:
                    j["status"], j["error"] = "failed", f"{type(e).__name__}: {e}"
                    j["log"].append(traceback.format_exc()[-1500:])
            finally:
                with self.lock:
                    j["finished"] = time.strftime("%Y-%m-%dT%H:%M:%S")
                    self._save(j)

        self.pool.submit(run)
        return dict(j)

    def get(self, jid: str):
        j = self.jobs.get(jid)
        return dict(j) if j else None

    def list(self, project=None):
        js = sorted(self.jobs.values(), key=lambda x: x["created"], reverse=True)
        return [dict(j) for j in js if project is None or j["project"] == project]
