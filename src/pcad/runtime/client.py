"""Asynchronous worker client with single-thread IPC queue, timeouts, and Qt signals."""

import json
import queue
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path
from typing import Any, Callable, Dict, Optional
from PySide6.QtCore import QObject, QTimer, Signal

from pcad.runtime.protocol import (
    BuildRequest, BuildResult, ExportRequest, ExportResult, WorkerError
)

class WorkerClient(QObject):
    build_started = Signal(str)        # req_id
    build_finished = Signal(object)    # BuildResult
    build_failed = Signal(object)      # WorkerError
    export_finished = Signal(object)   # ExportResult
    export_failed = Signal(str)        # error string

    def __init__(self, parent=None, timeout_sec: float = 25.0):
        super().__init__(parent)
        self.timeout_sec = timeout_sec
        self._proc: Optional[subprocess.Popen] = None
        self._proc_lock = threading.Lock()
        self._stderr_file = None
        
        # FIFO queue for requests to guarantee sequential IPC without race conditions
        self._queue: queue.Queue = queue.Queue()
        self._running = True
        self._active_req_id: Optional[str] = None
        
        # Debounce timer for UI spinbox changes
        self._debounce_timer = QTimer(self)
        self._debounce_timer.setSingleShot(True)
        self._debounce_timer.setInterval(200) # 200ms
        self._pending_request: Optional[BuildRequest] = None
        self._debounce_timer.timeout.connect(self._dispatch_pending_build)
        
        # Launch dedicated IPC worker thread
        self._ipc_thread = threading.Thread(target=self._ipc_loop, daemon=True)
        self._ipc_thread.start()
        
        # Pre-warm worker process in background immediately
        threading.Thread(target=self._ensure_worker_running, daemon=True).start()

    def _ensure_worker_running(self):
        with self._proc_lock:
            if self._proc is None or self._proc.poll() is not None:
                log_dir = Path(tempfile.gettempdir()) / "pcad_ipc"
                log_dir.mkdir(parents=True, exist_ok=True)
                stderr_log = log_dir / "worker_stderr.log"
                self._stderr_file = open(stderr_log, "a", encoding="utf-8")
                self._proc = subprocess.Popen(
                    [sys.executable, "-u", "-m", "pcad.runtime.worker_main"],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=self._stderr_file,
                    text=True,
                    bufsize=1
                )

    def restart_worker(self):
        """Kills and restarts the worker process (e.g. after a timeout or crash)."""
        with self._proc_lock:
            if self._proc:
                try:
                    self._proc.kill()
                    self._proc.wait(timeout=2.0)
                except Exception:
                    pass
                self._proc = None
            if self._stderr_file:
                try:
                    self._stderr_file.close()
                except Exception:
                    pass
                self._stderr_file = None
        self._ensure_worker_running()

    def cancel_pending(self):
        """Cancels any debounced build request currently waiting to fire."""
        if self._debounce_timer.isActive():
            self._debounce_timer.stop()
        self._pending_request = None

    def request_build_debounced(self, req: BuildRequest):
        """Enqueues build with 200ms debounce to avoid spamming worker while typing."""
        self._pending_request = req
        self._debounce_timer.start()

    def _dispatch_pending_build(self):
        if self._pending_request:
            req = self._pending_request
            self._pending_request = None
            self.request_build_immediate(req)

    def request_build_immediate(self, req: BuildRequest):
        self.cancel_pending()
        self._active_req_id = req.req_id
        self.build_started.emit(req.req_id)
        self._queue.put(("build", req))

    def request_export(self, req: ExportRequest):
        self._queue.put(("export", req))

    def _ipc_loop(self):
        """Dedicated single thread that handles all stdin/stdout communication with worker."""
        while self._running:
            try:
                item = self._queue.get(timeout=0.5)
            except queue.Empty:
                continue
                
            if item is None or not self._running:
                break
                
            req_type, req = item
            
            # If this is an obsolete build request that was superseded by a newer one, skip it
            if req_type == "build" and self._active_req_id != req.req_id:
                self._queue.task_done()
                continue
                
            try:
                self._ensure_worker_running()
                line_payload = json.dumps({"type": req_type, "payload": req.model_dump()}) + "\n"
                
                with self._proc_lock:
                    self._proc.stdin.write(line_payload)
                    self._proc.stdin.flush()
                    response_line = self._proc.stdout.readline()
                    
                if not response_line:
                    raise RuntimeError("Worker process closed pipe unexpectedly.")
                    
                resp_data = json.loads(response_line)
                
                if req_type == "build":
                    if resp_data.get("status") == "ok":
                        build_res = BuildResult(**resp_data["payload"])
                        # Emit only if this is still the active build request
                        if self._active_req_id == req.req_id:
                            self.build_finished.emit(build_res)
                    else:
                        err_data = resp_data.get("error", {})
                        err = WorkerError(**err_data)
                        if self._active_req_id == req.req_id:
                            self.build_failed.emit(err)
                            
                elif req_type == "export":
                    if resp_data.get("status") == "ok":
                        exp_res = ExportResult(**resp_data["payload"])
                        self.export_finished.emit(exp_res)
                    else:
                        err_msg = resp_data.get("error", {}).get("message_key", "Export failed")
                        self.export_failed.emit(err_msg)
                        
            except Exception as e:
                self.restart_worker()
                if req_type == "build" and self._active_req_id == req.req_id:
                    err = WorkerError(
                        req_id=req.req_id,
                        kind="kernel_crash",
                        message_key=str(e),
                        detail=str(e)
                    )
                    self.build_failed.emit(err)
                elif req_type == "export":
                    self.export_failed.emit(str(e))
            finally:
                self._queue.task_done()

    def close(self):
        self._running = False
        self._queue.put(None)
        with self._proc_lock:
            if self._proc:
                try:
                    self._proc.stdin.close()
                    self._proc.terminate()
                except Exception:
                    pass
                self._proc = None
            if self._stderr_file:
                try:
                    self._stderr_file.close()
                except Exception:
                    pass
                self._stderr_file = None
