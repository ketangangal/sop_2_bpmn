from abc import ABC, abstractmethod

from src.models.sop import SOPDocument


class BaseSOPParser(ABC):
    """Interface contract for all SOP parsers."""

    @abstractmethod
    async def parse(self, file_content: bytes) -> SOPDocument:
        """Parse raw file bytes into a structured SOPDocument."""
        ...
