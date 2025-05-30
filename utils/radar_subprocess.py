import subprocess
import sys
from fastapi.responses import JSONResponse


def agentic_radar_subprocess(command):
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace'
        )

        if result:
            if result.returncode != 0:
                print(f"Command failed with return code: {result.returncode}", file=sys.stderr)
                print(f"Error output: {result.stderr}", file=sys.stderr)
                return JSONResponse(
                    status_code=400,
                    content={
                        "success": False,
                        "messages": result.stderr
                    }
                )
            print(result.stdout)
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "messages": result.stdout.strip()
                }
            )
        return None
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {e}", file=sys.stderr)
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "messages": e
            }
        )
