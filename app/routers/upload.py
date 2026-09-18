import logging
import tempfile

import aiofiles
from fastapi import APIRouter, HTTPException, UploadFile

from app.libs.b2 import b2_upload_file

logger = logging.getLogger(__name__)

router = APIRouter()

CHUNK_SIZE = 1024 * 1024  # 1MB


@router.post("/upload", status_code=201)
async def upload_File(file: UploadFile):
    try:
        with tempfile.NamedTemporaryFile() as temp_file:
            filename = temp_file.name
            logger.info(f"Saving uploaded file temporarily to {filename}")
            async with aiofiles.open(filename, "wb") as f:
                while chunk := await file.read(CHUNK_SIZE):
                    await f.write(chunk)

            file_url = b2_upload_file(local_file=filename, file_name=file.filename)
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="There was an error uploading the file",
        )

    return {"detail": f"Succesfully uploaded {file.filename}", "file_url": file_url}
