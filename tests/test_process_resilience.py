"""Tests for IPC timeout, process crashes, cancellation, and code error reporting."""

import time
import pytest
from PySide6.QtCore import QCoreApplication

from pcad.runtime.client import WorkerClient
from pcad.runtime.protocol import BuildRequest, BuildResult, WorkerError
from pcad.runtime.worker_main import process_build, CodeExecError

@pytest.fixture(scope="session")
def qapp():
    app = QCoreApplication.instance()
    if app is None:
        app = QCoreApplication([])
    return app

def test_syntax_error_reporting():
    """Verify that Python syntax errors report exact line number and line snippet."""
    code = (
        "import build123d as bd\n"
        "with bd.BuildPart() as p:\n"
        "    bd.Box(20, 20, 10\n"  # missing closing parenthesis on line 3
    )
    req = BuildRequest(req_id="syntax_err_1", source="code", code=code)
    with pytest.raises(CodeExecError) as exc_info:
        process_build(req)
    
    err = exc_info.value.worker_error
    assert err.kind == "code_error"
    assert err.line_no == 3
    assert "SyntaxError" in err.message_key

def test_runtime_error_reporting():
    """Verify that Python runtime exceptions report exact line number and snippet."""
    code = (
        "import build123d as bd\n"
        "a = 10\n"
        "b = 0\n"
        "val = a / b\n"  # ZeroDivisionError on line 4
        "with bd.BuildPart() as p:\n"
        "    bd.Box(val, 20, 10)\n"
        "result = p.part\n"
    )
    req = BuildRequest(req_id="runtime_err_1", source="code", code=code)
    with pytest.raises(CodeExecError) as exc_info:
        process_build(req)
        
    err = exc_info.value.worker_error
    assert err.kind == "code_error"
    assert err.line_no == 4
    assert "ZeroDivisionError" in err.message_key
    assert "val = a / b" in (err.line_text or "")

def test_worker_client_timeout_and_recovery(qapp):
    """Verify WorkerClient terminates an infinite loop and recovers for subsequent builds."""
    client = WorkerClient(timeout_sec=1.5)
    
    results = []
    errors = []
    
    client.build_finished.connect(lambda res: results.append(res))
    client.build_failed.connect(lambda err: errors.append(err))
    
    # 1. Send infinite loop
    inf_req = BuildRequest(
        req_id="timeout_req",
        source="code",
        code="while True:\n    pass\n"
    )
    client.request_build_immediate(inf_req)
    
    t0 = time.time()
    while not errors and time.time() - t0 < 12.0:
        qapp.processEvents()
        time.sleep(0.05)
        
    assert len(errors) == 1, "Expected timeout error"
    assert errors[0].kind == "timeout"
    assert "Zaman Aşımı" in errors[0].message_key or "timeout" in errors[0].message_key.lower()
    
    # 2. Immediately send a valid request to confirm client & worker recovered
    errors.clear()
    valid_code = (
        "import build123d as bd\n"
        "with bd.BuildPart() as p:\n"
        "    bd.Box(30, 20, 10)\n"
        "result = p.part\n"
    )
    valid_req = BuildRequest(
        req_id="recovery_req",
        source="code",
        code=valid_code
    )
    client.request_build_immediate(valid_req)
    
    t0 = time.time()
    while not results and not errors and time.time() - t0 < 10.0:
        qapp.processEvents()
        time.sleep(0.05)
        
    assert len(results) == 1, f"Worker failed to recover after timeout: errors={errors}"
    assert results[0].req_id == "recovery_req"
    
    client.close()

def test_worker_client_crash_recovery(qapp):
    """Verify WorkerClient recovers when the worker process abruptly exits (crash)."""
    client = WorkerClient(timeout_sec=5.0)
    
    results = []
    errors = []
    client.build_finished.connect(lambda res: results.append(res))
    client.build_failed.connect(lambda err: errors.append(err))
    
    # Send crash code
    crash_req = BuildRequest(
        req_id="crash_req",
        source="code",
        code="import os; os._exit(1)\n"
    )
    client.request_build_immediate(crash_req)
    
    t0 = time.time()
    while not errors and time.time() - t0 < 8.0:
        qapp.processEvents()
        time.sleep(0.05)
        
    assert len(errors) == 1
    assert errors[0].kind == "kernel_crash"
    
    # Immediately send valid request
    errors.clear()
    valid_code = (
        "import build123d as bd\n"
        "with bd.BuildPart() as p:\n"
        "    bd.Box(25, 25, 10)\n"
        "result = p.part\n"
    )
    valid_req = BuildRequest(
        req_id="recovery_post_crash",
        source="code",
        code=valid_code
    )
    client.request_build_immediate(valid_req)
    
    t0 = time.time()
    while not results and not errors and time.time() - t0 < 10.0:
        qapp.processEvents()
        time.sleep(0.05)
        
    assert len(results) == 1, f"Worker failed to recover after crash: errors={errors}"
    assert results[0].req_id == "recovery_post_crash"
    
    client.close()
