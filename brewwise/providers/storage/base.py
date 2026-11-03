from abc import ABC, abstractmethod
from typing import Optional


class StorageProvider(ABC):
    @abstractmethod
    async def upload(self, file_bytes: bytes, filename: str, content_type: str = "image/jpeg") -> str:
        """Uploads a file and returns its storage path or identifier."""
        pass

    @abstractmethod
    async def get_url(self, file_id: str) -> str:
        """Returns the accessible URL or local path for the stored file."""
        pass

    @abstractmethod
    async def delete(self, file_id: str) -> bool:
        """Deletes a file by its identifier."""
        pass
