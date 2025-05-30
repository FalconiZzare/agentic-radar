from pathlib import Path
import shutil
from datetime import datetime


UPLOAD_DIR = Path("tmp")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

async def radar_scan(framework, file):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_location = UPLOAD_DIR / file.filename

    with file.file as src, open(file_location, "wb") as dst:
        shutil.copyfileobj(src, dst)

    return {
        "file_name": file.filename,
        "framework": framework,
        "saved_to": str(file_location),
        "timestamp": timestamp,
    }