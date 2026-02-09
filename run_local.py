"""
run_local.py - Custom Web UI launcher for KAgent Vision

Spawns the ADK api_server as a subprocess, proxies API calls, and serves a
custom single-file UI on port 5001.

Usage:
    source .venv/bin/activate
    GOOGLE_API_KEY="$GEMINI_API_KEY" python run_local.py
"""

import asyncio
import atexit
import os
import signal
import subprocess
import sys
import time

import httpx
import uvicorn
from fastapi import FastAPI, Request, UploadFile, File
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

ADK_PORT = 8080
UI_PORT = 5001
ADK_BASE = f"http://localhost:{ADK_PORT}"

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(PROJECT_DIR, "static")
OUTPUTS_DIR = os.path.join(PROJECT_DIR, "outputs")

app = FastAPI()
adk_proc: subprocess.Popen | None = None
http_client: httpx.AsyncClient | None = None


@app.on_event("startup")
async def startup():
    global http_client
    http_client = httpx.AsyncClient(timeout=httpx.Timeout(600.0))


@app.on_event("shutdown")
async def shutdown():
    if http_client:
        await http_client.aclose()


def start_adk_server():
    global adk_proc
    env = {**os.environ, "MCP_LOCAL": "1"}
    adk_proc = subprocess.Popen(
        [sys.executable, "-m", "google.adk.cli", "api_server", ".", "--port", str(ADK_PORT)],
        env=env,
        cwd=os.path.dirname(os.path.abspath(__file__)),
    )

    # Wait for ADK to be ready
    for _ in range(60):
        try:
            resp = httpx.get(f"{ADK_BASE}/list-apps", timeout=2)
            if resp.status_code == 200:
                print(f"ADK api_server ready on port {ADK_PORT}")
                return
        except httpx.ConnectError:
            pass
        time.sleep(1)

    print("ERROR: ADK api_server did not start in time", file=sys.stderr)
    sys.exit(1)


def cleanup():
    if adk_proc and adk_proc.poll() is None:
        adk_proc.terminate()
        try:
            adk_proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            adk_proc.kill()


atexit.register(cleanup)


os.makedirs(OUTPUTS_DIR, exist_ok=True)
app.mount("/outputs", StaticFiles(directory=OUTPUTS_DIR), name="outputs")


@app.get("/")
async def serve_ui():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))


@app.post("/upload")
async def upload_image(file: UploadFile = File(...)):
    """Save an uploaded image to outputs/ and return its path."""
    ts = time.strftime("%Y%m%d_%H%M%S")
    ms = int((time.time() % 1) * 1000)
    ext = os.path.splitext(file.filename or "image.jpg")[1] or ".jpg"
    fname = f"upload_{ts}_{ms:03d}{ext}"
    fpath = os.path.join(OUTPUTS_DIR, fname)
    contents = await file.read()
    with open(fpath, "wb") as f:
        f.write(contents)
    return JSONResponse({"ok": True, "path": f"outputs/{fname}", "filename": fname})


@app.api_route("/api/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_to_adk(request: Request, path: str):
    url = f"{ADK_BASE}/{path}"
    headers = {k: v for k, v in request.headers.items() if k.lower() != "host"}

    body = await request.body()

    if path == "run_sse":
        # SSE streaming proxy — must keep response open until stream ends
        req = http_client.build_request(
            method=request.method,
            url=url,
            headers=headers,
            content=body,
        )
        response = await http_client.send(req, stream=True)

        async def stream():
            try:
                async for chunk in response.aiter_bytes():
                    yield chunk
            finally:
                await response.aclose()

        return StreamingResponse(
            stream(),
            status_code=response.status_code,
            media_type="text/event-stream",
        )
    else:
        response = await http_client.request(
            method=request.method,
            url=url,
            headers=headers,
            content=body,
        )
        # Filter hop-by-hop headers
        skip = {"transfer-encoding", "content-encoding", "content-length", "connection"}
        resp_headers = {k: v for k, v in response.headers.items() if k.lower() not in skip}
        return StreamingResponse(
            iter([response.content]),
            status_code=response.status_code,
            headers=resp_headers,
        )


def main():
    print("Starting ADK api_server...")
    start_adk_server()
    print(f"Starting custom UI on http://localhost:{UI_PORT}")
    uvicorn.run(app, host="0.0.0.0", port=UI_PORT, log_level="info")


if __name__ == "__main__":
    signal.signal(signal.SIGINT, lambda *_: sys.exit(0))
    main()
