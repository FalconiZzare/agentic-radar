from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Form, File, UploadFile
from fastapi.responses import JSONResponse

from prints.print_green import print_green
from prints.print_red import print_red
from fastapi.middleware.cors import CORSMiddleware
from utils.radar_subprocess import execute_subprocess
from utils.radar_scan import radar_scan
from utils.mcp_scan import scan_mcp


@asynccontextmanager
async def lifespan(app: FastAPI):
    print_green("🚀 Server started")

    yield

    print_red("🛑 Server shutting down")


app = FastAPI(
    title="Agentic Radar",
    description="Agentic Workflows Scanning Endpoints.",
    lifespan=lifespan
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://n8n-888533232611.us-central1.run.app", "https://api.octopi.ai"],
    allow_credentials=True,
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": "Octopi Watch Server is running", "status": "ok"}


@app.get("/ok")
async def health_check():
    res = await execute_subprocess(['agentic-radar', '--version'])
    return JSONResponse(
        status_code=res["status_code"],
        content={
            "success": res["success"],
            "message": res["message"]
        }
    )

@app.get("/mcp-ok")
async def health_check_mcp():
    res = await execute_subprocess(['mcp-scan', 'version'])
    return JSONResponse(
        status_code=res["status_code"],
        content={
            "success": res["success"],
            "message": res["message"]
        }
    )

@app.post("/scan")
async def scan_endpoint(
        framework: str = Form(...),
        user_id: str = Form(...),
        scan_id: str = Form(...),
        file_name: str = Form(...),
        presign_duration: int = Form(...),
):
    return await radar_scan(framework, file_name, user_id, scan_id, presign_duration)

@app.post("/scan-mcp")
async def scan_mcp_endpoint(
        server_type: str = Form(...),
        url: str = Form(...)
):
    return await scan_mcp(server_type, url)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)
