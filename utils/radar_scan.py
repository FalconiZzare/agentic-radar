import os
import glob
from pathlib import Path
import shutil
from datetime import datetime
from dotenv import load_dotenv
from fastapi.responses import JSONResponse
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
import logging

from utils.radar_subprocess import execute_subprocess
from utils.helpers import replace_mask_logo

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

UPLOAD_DIR = Path("tmp")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# S3 Configuration - Set these via environment variables
S3_BUCKET_NAME = os.getenv('S3_BUCKET_NAME')
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_REGION = os.getenv('AWS_REGION', 'ap-south-1')

ALLOWED_FRAMEWORKS = ['n8n']
ALLOWED_FILETYPES = ['.json']


def get_s3_client():
    """Initialize and return S3 client"""
    try:
        # Always prioritize explicitly provided credentials
        if AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY:
            return boto3.client(
                's3',
                aws_access_key_id=AWS_ACCESS_KEY_ID,
                aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                region_name=AWS_REGION,
                endpoint_url=f"https://s3.{AWS_REGION}.amazonaws.com"
            )
        else:
            logger.warning("AWS_ACCESS_KEY_ID or AWS_SECRET_ACCESS_KEY not found in environment variables")
            # Use default credentials (IAM role, shared credentials, etc.)
            return boto3.client('s3', region_name=AWS_REGION)
    except NoCredentialsError:
        logger.error("AWS credentials not found")
        return None
    except Exception as e:
        logger.error(f"Error initializing S3 client: {str(e)}")
        return None


def download_input_from_s3(file_path: str, s3_key: str) -> dict:
    """Download a file from S3 using boto3"""
    s3_client = get_s3_client()
    if not s3_client:
        return {
            "success": False,
            "error": "Failed to initialize S3 client"
        }

    try:
        file_path = UPLOAD_DIR / file_path
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Verify the directory was created
        if not file_path.parent.exists():
            return {
                "success": False,
                "error": f"Failed to create directory: {file_path.parent}"
            }

        # Check write permissions
        if not os.access(file_path.parent, os.W_OK):
            return {
                "success": False,
                "error": f"No write permission to directory: {file_path.parent}"
            }

        s3_client.download_file(
            Bucket=S3_BUCKET_NAME,
            Key=s3_key,
            Filename=str(file_path)
        )

        return {
            "success": True,
        }

    except ClientError as e:
        error_msg = f"AWS S3 download error: {e}"
        logger.error(error_msg)
        return {
            "success": False,
            "error": error_msg,
            "error_code": e.response['Error']['Code']
        }
    except Exception as e:
        error_msg = f"S3 Download error: {str(e)}"
        logger.error(error_msg)
        return {
            "success": False,
            "error": error_msg
        }


def upload_report_to_s3(file_path: str, s3_key: str) -> dict:
    """
    Change Branding & Upload HTML report file to S3

    Args:
        file_path: Local path to the HTML report file
        s3_key: S3 object key for the uploaded file

    Returns:
        Dict with upload result
    """
    s3_client = get_s3_client()
    if not s3_client:
        return {
            "success": False,
            "error": "Failed to initialize S3 client"
        }

    try:
        # Check if file exists
        if not os.path.exists(file_path):
            return {
                "success": False,
                "error": f"Report file not found: {file_path}"
            }

        octopi_svg = """
        <g>
            <image href="https://www.octopi.ai/images/logo/logo_full.svg" x="10" y="10" height="44" width="250"/>
        </g>
        """

        replace_mask_logo(file_path, octopi_svg)

        # Upload file to S3
        s3_client.upload_file(
            file_path,
            S3_BUCKET_NAME,
            s3_key,
            ExtraArgs={
                'ContentType': 'text/html',
                'Metadata': {
                    'ContentDisposition': 'inline',
                    'source': 'octopi-watch',
                    'upload_time': datetime.now().isoformat()
                }
            }
        )

        return {
            "success": True,
            "s3_key": s3_key,
            "bucket": S3_BUCKET_NAME,
            "s3_url": f"https://{S3_BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com/{s3_key}"
        }

    except ClientError as e:
        error_msg = f"AWS S3 upload error: {e}"
        logger.error(error_msg)
        return {
            "success": False,
            "error": error_msg,
            "error_code": e.response['Error']['Code']
        }
    except Exception as e:
        error_msg = f"Upload error: {str(e)}"
        logger.error(error_msg)
        return {
            "success": False,
            "error": error_msg
        }


def generate_presigned_url(s3_key: str, expiration: int = 3600) -> dict:
    """
    Generate a presigned URL for the S3 object

    Args:
        s3_key: S3 object key
        expiration: URL expiration time in seconds (default: 1 hour)

    Returns:
        Dict with presigned URL information
    """
    s3_client = get_s3_client()
    if not s3_client:
        return {
            "success": False,
            "error": "Failed to initialize S3 client"
        }

    try:
        presigned_url = s3_client.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': S3_BUCKET_NAME,
                'Key': s3_key
            },
            ExpiresIn=expiration
        )

        expires_at = datetime.now().timestamp() + expiration

        return {
            "success": True,
            "presigned_url": presigned_url,
            "expires_in_seconds": expiration,
            "expires_at": datetime.fromtimestamp(expires_at).isoformat()
        }

    except ClientError as e:
        error_msg = f"AWS S3 presigned URL error: {e}"
        logger.error(error_msg)
        return {
            "success": False,
            "error": error_msg,
            "error_code": e.response['Error']['Code']
        }
    except Exception as e:
        error_msg = f"Presigned URL generation error: {str(e)}"
        logger.error(error_msg)
        return {
            "success": False,
            "error": error_msg
        }


def clear_tmp_directory():
    """Cross-platform function to clear tmp directory contents"""
    for item in glob.glob(os.path.join(UPLOAD_DIR, "*")):
        try:
            if os.path.isfile(item):
                os.remove(item)
            elif os.path.isdir(item):
                shutil.rmtree(item)
        except Exception as e:
            logger.warning(f"Error removing {item}: {e}")


async def radar_scan(framework, file_name, user_id, scan_id, presign_duration):
    report_filename = f"report_{file_name}.html"
    report_path = UPLOAD_DIR / user_id / scan_id / report_filename

    # S3 key for the report
    s3_report_key = f"results/{user_id}/{scan_id}/{report_filename}"

    # Validate frameworkk
    if framework not in ALLOWED_FRAMEWORKS:
        error_msg = f"Framework '{framework}' is not allowed. Allowed frameworks:[{', '.join(ALLOWED_FRAMEWORKS)}]"
        logger.error(error_msg)
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "message": error_msg,
                "error_type": "invalid_framework"
            }
        )

    try:
        # Download job file from S3
        try:
            s3_key = f"inputs/{user_id}/{scan_id}/{file_name}"
            file_location = f"{user_id}/{scan_id}/{file_name}"
            download_result = download_input_from_s3(file_location, s3_key)

            if not download_result["success"]:
                logger.error(f"S3 Download failed: {download_result['error']}")
                return JSONResponse(
                    status_code=400,
                    content={
                        "success": False,
                        "message": download_result["error"],
                        "error_type": "s3_download_error",
                    }
                )
        except Exception as e:
            error_msg = f"Unexpected error during S3 download: {str(e)}"
            logger.error(error_msg)
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "message": error_msg,
                    "error_type": "file_download_error"
                }
            )

        # Run the radar scan
        try:
            res = await execute_subprocess(
                ["agentic-radar", "scan", framework, "-i", str(UPLOAD_DIR / user_id / scan_id), "-o", str(report_path)]
            )
        except Exception as e:
            error_msg = f"Radar scan subprocess failed: {str(e)}"
            logger.error(error_msg)
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "message": error_msg,
                    "error_type": "radar_scan_error"
                }
            )

        # Check if radar scan was successful
        if not res["success"]:
            logger.error(f"Radar scan failed: {res['message']}")
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "message": res["message"],
                    "error_type": "radar_scan_failed",
                    "file_name": file_name,
                    "framework": framework
                }
            )

        # Check if report file was generated
        if not os.path.exists(report_path):
            error_msg = f"Report file not generated after scan: {report_path}"
            logger.error(error_msg)
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "message": error_msg,
                    "error_type": "report_generation_error",
                    "file_name": file_name,
                    "framework": framework,
                }
            )

        # Upload report to S3
        upload_result = upload_report_to_s3(str(report_path), s3_report_key)

        if not upload_result["success"]:
            error_msg = f"Failed to upload report to S3: {upload_result['error']}"
            logger.error(error_msg)
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "message": error_msg,
                    "error_type": "s3_upload_error",
                    "file_name": file_name,
                    "framework": framework,
                    "s3_error_details": upload_result.get("error_code")
                }
            )

        # Generate presigned URL for the uploaded report
        presigned_result = generate_presigned_url(s3_report_key, expiration=presign_duration)

        if not presigned_result["success"]:
            error_msg = f"Failed to generate presigned URL: {presigned_result['error']}"
            logger.error(error_msg)
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "message": error_msg,
                    "error_type": "presigned_url_error",
                    "file_name": file_name,
                    "framework": framework,
                    "s3_error_details": presigned_result.get("error_code")
                }
            )

        # All processes succeeded - return success response
        response_data = {
            "success": True,
            "file_name": file_name,
            "framework": framework,
            "message": res["message"],
            "report_name": report_filename,
            "report_content": {
                "success": True,
                "presigned_url": presigned_result["presigned_url"],
                "presigned_expires_at": presigned_result["expires_at"],
                "presigned_expires_in": presigned_result["expires_in_seconds"]
            }
        }

        return JSONResponse(
            status_code=200,
            content=response_data
        )

    except Exception as e:
        error_msg = f"Unexpected error during radar scan process: {str(e)}"
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
        # Clean up uploaded files and local reports
        try:
            clear_tmp_directory()
        except Exception as e:
            logger.warning(f"Error during cleanup: {e}")
