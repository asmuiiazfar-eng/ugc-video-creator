import boto3
from botocore.config import Config
from typing import Optional
from urllib.parse import urlparse

from app.config import get_settings

settings = get_settings()


def _get_client():
    """Get S3-compatible R2 client."""
    return boto3.client(
        "s3",
        endpoint_url=settings.R2_ENDPOINT,
        aws_access_key_id=settings.R2_ACCESS_KEY_ID,
        aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
        config=Config(
            signature_version="s3v4",
            retries={"max_attempts": 3, "mode": "standard"},
        ),
    )


async def upload_file(file_bytes: bytes, key: str, content_type: str = "application/octet-stream") -> str:
    """Upload a file to R2. Returns the public URL."""
    client = _get_client()
    client.put_object(
        Bucket=settings.R2_BUCKET_NAME,
        Key=key,
        Body=file_bytes,
        ContentType=content_type,
    )
    return f"{settings.R2_ENDPOINT}/{settings.R2_BUCKET_NAME}/{key}"


async def get_presigned_url(key: str, expires_in: int = 3600) -> str:
    """Generate a presigned URL for uploading a file."""
    client = _get_client()
    url = client.generate_presigned_url(
        ClientMethod="put_object",
        Params={
            "Bucket": settings.R2_BUCKET_NAME,
            "Key": key,
        },
        ExpiresIn=expires_in,
    )
    return url


async def delete_file(key: str) -> None:
    """Delete a file from R2."""
    client = _get_client()
    client.delete_object(
        Bucket=settings.R2_BUCKET_NAME,
        Key=key,
    )


def get_key_from_url(url: str) -> str:
    """Extract the object key from a full R2 URL."""
    prefix = f"{settings.R2_ENDPOINT}/{settings.R2_BUCKET_NAME}/"
    if url.startswith(prefix):
        return url[len(prefix):]
    parsed = urlparse(url)
    return parsed.path.lstrip("/")