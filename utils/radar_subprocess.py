import subprocess
import sys


async def execute_subprocess(command):
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

                return {
                    "status_code": 400,
                    "success": False,
                    "message": result.stderr.strip()
                }

            return {
                "status_code": 200,
                "success": True,
                "message": result.stdout.strip()
            }
        return None
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {e}", file=sys.stderr)
        return {
            "status_code": 500,
            "success": False,
            "message": e
        }
