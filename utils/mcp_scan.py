import os
from pathlib import Path
import logging
from dotenv import load_dotenv
from fastapi.responses import JSONResponse
import json

from utils.radar_scan import clear_tmp_directory
from utils.radar_subprocess import execute_subprocess

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

UPLOAD_DIR = Path("tmp")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_SERVER_TYPES = ['sse', 'http']


async def scan_mcp(server_type: str, url: str):
    # Wrap the entire function logic in a single try/finally block to guarantee cleanup
    try:
        # --- Validation ---
        if server_type not in ALLOWED_SERVER_TYPES:
            error_msg = f"Unsupported server type. Scannable server types: [{', '.join(ALLOWED_SERVER_TYPES)}]"
            logger.error(error_msg)
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "message": error_msg,
                    "error_type": "invalid server type"
                }
            )

        # --- Directory Setup ---
        safe_url_part = url.split("://")[-1].replace("/", "_").replace(".", "_")
        file_path = UPLOAD_DIR / f"{server_type}_servers/{safe_url_part}"

        # Call .mkdir() on file_path itself to create the full directory path recursively.
        file_path.mkdir(parents=True, exist_ok=True)

        config_file_path = file_path / "config.json"

        # These checks now correctly reference the created directory
        if not config_file_path.parent.exists():
            return {
                "success": False,
                "error": f"Failed to create directory: {config_file_path.parent}"
            }

        if not os.access(config_file_path.parent, os.W_OK):
            return {
                "success": False,
                "error": f"No write permission to directory: {config_file_path.parent}"
            }

        server_key = f"{server_type}_server"

        mcp_config = {
            "mcp": {
                "servers": {
                    server_key: {
                        "type": server_type,
                        "url": url
                    }
                }
            }
        }

        # --- Write Config File ---
        try:
            with open(config_file_path, "w") as f:
                json.dump(mcp_config, f, indent=2)

        except IOError as e:
            error_msg = f"Failed to write config file to {config_file_path}: {str(e)}"
            logger.error(error_msg)
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "message": error_msg,
                    "error_type": "file_write_error"
                }
            )

        # --- Execute Subprocess ---
        try:
            res = await execute_subprocess(['mcp-scan', "scan", str(config_file_path), "--json"])

        except Exception as e:
            error_msg = f"MCP scan subprocess failed: {str(e)}"
            logger.error(error_msg)
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "message": error_msg,
                    "error_type": "mcp_scan_error"
                }
            )

        if not res["success"]:
            logger.error(f"MCP scan failed: {res['message']}")
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "message": res["message"],
                    "error_type": "mcp_scan_failed",
                    "server_type": server_type,
                    "url": url
                }
            )

        # --- Success Return ---
        status_code = res.get("status_code", 200)

        return JSONResponse(
            status_code=status_code,
            content={
                "success": res["success"],
                "message": json.loads(res["message"])
            }
        )

    except Exception as e:
        error_msg = f"Unexpected error during scan process: {str(e)}"
        logger.error(error_msg)
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "message": error_msg,
                "error_type": "unexpected_error"
            }
        )

    finally:
        # This finally block is guaranteed to execute whenever the function exits (returns or raises)
        try:
            clear_tmp_directory()
        except Exception as e:
            logger.warning(f"Error during cleanup: {e}")