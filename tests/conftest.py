import socket
import subprocess
import sys
import time
import os
from collections.abc import Generator
import pytest
from fastapi import FastAPI, Request, Response
from fastapi.testclient import TestClient

from hls_scte35_manipulator_server import create_app

ORIGIN_HOST = "127.0.0.1"
ORIGIN_PORT = 9999

def _with_no_proxy_env() -> dict[str, str]:
    env = os.environ.copy()
    no_proxy_targets = "127.0.0.1,localhost,::1"
    for key in ("NO_PROXY", "no_proxy"):
        current = env.get(key, "").strip()
        env[key] = f"{current},{no_proxy_targets}".strip(",") if current else no_proxy_targets
    return env

def create_origin_app() -> FastAPI:
    origin = FastAPI(title="test-origin")

    @origin.put("/{full_path:path}")
    async def proxy_put(full_path: str, request: Request) -> Response:
        body = await request.body()
        return Response(content=body, status_code=200)

    return origin

def _wait_for_origin(timeout_seconds: float = 10.0) -> None:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        try:
            with socket.create_connection((ORIGIN_HOST, ORIGIN_PORT), timeout=0.3):
                return
        except OSError:
            time.sleep(0.1)
    raise RuntimeError(f"Origin server did not start on {ORIGIN_HOST}:{ORIGIN_PORT}")

@pytest.fixture(scope="session", autouse=True)
def origin_server() -> Generator[None, None, None]:
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "tests.conftest:create_origin_app",
            "--factory",
            "--host",
            ORIGIN_HOST,
            "--port",
            str(ORIGIN_PORT),
            "--log-level",
            "warning",
        ],
        env=_with_no_proxy_env(),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    try:
        _wait_for_origin()
        yield
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)

@pytest.fixture
def appargs():
    return dict(
        origin_base_url=f"http://{ORIGIN_HOST}:{ORIGIN_PORT}",
        profile_path="default.json",
        timeout_seconds=10.0,
        trust_env=False)  