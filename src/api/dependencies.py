from functools import lru_cache

from src.config import get_settings
from src.generator.bpmn_builder import BPMNBuilder
from src.generator.bpmn_xml_writer import BPMNXMLWriter
from src.generator.layout import LayoutEngine
from src.parser.docx_parser import DocxSOPParser
from src.parser.llm_analyzer import LLMSOPAnalyzer


@lru_cache
def get_parser() -> DocxSOPParser:
    """Return the SOP parser. Swap implementation here to change parsing strategy."""
    settings = get_settings()
    analyzer = LLMSOPAnalyzer(
        api_key=settings.azure_openai_api_key,
        azure_endpoint=settings.azure_openai_endpoint,
        api_version=settings.azure_openai_api_version,
        model=settings.azure_openai_deployment,
    )
    return DocxSOPParser(llm_analyzer=analyzer)


def get_builder() -> BPMNBuilder:
    return BPMNBuilder()


def get_layout_engine() -> LayoutEngine:
    return LayoutEngine()


def get_xml_writer() -> BPMNXMLWriter:
    return BPMNXMLWriter()
