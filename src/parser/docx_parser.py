from io import BytesIO

from docx import Document as DocxDocument

from src.models.sop import SOPDocument
from src.parser.base import BaseSOPParser
from src.parser.llm_analyzer import LLMSOPAnalyzer


class DocxSOPParser(BaseSOPParser):
    """Parses .docx SOP files by extracting text and delegating to LLM analysis."""

    def __init__(self, llm_analyzer: LLMSOPAnalyzer) -> None:
        self._llm_analyzer = llm_analyzer

    async def parse(self, file_content: bytes) -> SOPDocument:
        raw_text = self._extract_text(file_content)
        return await self._llm_analyzer.analyze(raw_text)

    def _extract_text(self, file_content: bytes) -> str:
        """Extract all paragraph text from a .docx file."""
        doc = DocxDocument(BytesIO(file_content))
        lines: list[str] = []
        for para in doc.paragraphs:
            text = para.text.strip()
            if text:
                lines.append(text)
        return "\n".join(lines)
