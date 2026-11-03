import os
from pathlib import Path
from brewwise.providers.storage.base import StorageProvider


class LocalStorageProvider(StorageProvider):
    def __init__(self, base_dir: str = "./uploads"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    async def upload(self, file_bytes: bytes, filename: str, content_type: str = "image/jpeg") -> str:
        file_path = self.base_dir / filename
        with open(file_path, "wb") as f:
            f.write(file_bytes)
        return filename

    async def get_url(self, file_id: str) -> str:
        return f"/uploads/{file_id}"

    async def delete(self, file_id: str) -> bool:
        file_path = self.base_dir / file_id
        if file_path.exists():
            os.remove(file_path)
            return True
        return False
