import uuid
from pathlib import Path
from typing import Optional

import aiofiles

from fastapi import UploadFile

from application.utilities.config import settings
from application.utilities.exceptions import FileSizeLimitExceededException, InvalidFileTypeException


ALLOWED_IMAGE_TYPES = ["image/jpeg", "image/png", "image/gif", "image/webp"]
MAX_FILE_SIZE_MB = 5
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024


class FileService:
    def __init__(self) -> None:
        self.upload_dir = Path(settings.upload_dir)
        self.upload_dir.mkdir(exist_ok=True)

    async def save_upload(self, file: UploadFile) -> str:
        if file.content_type not in ALLOWED_IMAGE_TYPES:
            raise InvalidFileTypeException(ALLOWED_IMAGE_TYPES)

        content = await file.read()
        if len(content) > MAX_FILE_SIZE_BYTES:
            raise FileSizeLimitExceededException(MAX_FILE_SIZE_MB)

        extension = self._get_extension(file.filename or "")
        filename = f"{uuid.uuid4()}{extension}"
        file_path = self.upload_dir / filename

        async with aiofiles.open(file_path, "wb") as f:
            await f.write(content)

        return filename

    async def delete_file(self, filename: str) -> bool:
        file_path = self.upload_dir / filename
        if file_path.exists():
            file_path.unlink()
            return True
        return False

    def get_file_url(self, filename: Optional[str], base_url: str) -> Optional[str]:
        if not filename:
            return None
        return f"{base_url}/uploads/{filename}"

    def _get_extension(self, filename: str) -> str:
        if "." in filename:
            return f".{filename.rsplit('.', 1)[1].lower()}"
        return ".jpg"


file_service = FileService()
