from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Form, File, UploadFile
from fastapi.responses import JSONResponse

from prints.print_green import print_green
from prints.print_red import print_red
from fastapi.middleware.cors import CORSMiddleware
from utils.radar_subprocess import agentic_radar_subprocess
from utils.radar_scan import radar_scan


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
    allow_origins=["http://localhost:5000", "https://api.octopi.ai"],
    allow_credentials=True,
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": "Agentic Radar Server is running", "status": "ok"}


@app.get("/ok")
async def health_check():
    res = await agentic_radar_subprocess(['agentic-radar', '--version'])
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
        file: UploadFile = File(...)
):
    return await radar_scan(framework, file, file_name, user_id, scan_id)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)
