import io

from fastapi import HTTPException, UploadFile

READ_CHUNK_SIZE = 1024 * 1024


async def read_upload_file(
    file: UploadFile,
    max_size_mb: int,
) -> bytes:
    max_size_bytes = max_size_mb * 1024 * 1024
    contents = io.BytesIO()
    size = 0

    while chunk := await file.read(READ_CHUNK_SIZE):
        size += len(chunk)

        if size > max_size_bytes:
            raise HTTPException(
                status_code=413,
                detail=f"Uploaded file is too large. Maximum size is {max_size_mb} MB.",
            )

        contents.write(chunk)

    return contents.getvalue()
