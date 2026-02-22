import logging
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import HTMLResponse, Response

from src.api.dependencies import get_builder, get_layout_engine, get_parser, get_xml_writer

logger = logging.getLogger(__name__)

TEMPLATES_DIR = Path(__file__).parent.parent / "templates"

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def ui():
    """Serve the upload UI."""
    html = (TEMPLATES_DIR / "index.html").read_text()
    return HTMLResponse(content=html)


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "sop-to-bpmn"}


@router.post(
    "/convert",
    response_class=Response,
    responses={200: {"content": {"application/xml": {}}, "description": "BPMN 2.0 XML output"}},
)
async def convert_sop_to_bpmn(file: UploadFile = File(...)):
    """Upload a .docx SOP file and receive BPMN 2.0 XML.

    The pipeline: Parse .docx → LLM Analysis → BPMN Model → Layout → XML
    """
    if not file.filename or not file.filename.endswith(".docx"):
        raise HTTPException(
            status_code=400,
            detail="Only .docx files are supported. Please upload a .docx file.",
        )

    try:
        file_content = await file.read()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read file: {e}")

    try:
        # Step 1: Parse SOP (extract text + LLM analysis)
        parser = get_parser()
        sop_document = await parser.parse(file_content)
        logger.info("Parsed SOP: %s with %d elements", sop_document.title, len(sop_document.elements))

        # Step 2: Build BPMN graph
        builder = get_builder()
        bpmn_process = builder.build(sop_document)
        logger.info("Built BPMN: %d nodes, %d flows", len(bpmn_process.nodes), len(bpmn_process.sequence_flows))

        # Step 3: Apply layout
        layout_engine = get_layout_engine()
        layout_engine.apply_layout(bpmn_process)

        # Step 4: Serialize to XML
        xml_writer = get_xml_writer()
        bpmn_xml = xml_writer.write(bpmn_process)

    except Exception as e:
        logger.exception("Conversion failed")
        raise HTTPException(status_code=422, detail=f"Failed to convert SOP to BPMN: {e}")

    output_filename = file.filename.replace(".docx", ".bpmn")
    return Response(
        content=bpmn_xml,
        media_type="application/xml",
        headers={"Content-Disposition": f'attachment; filename="{output_filename}"'},
    )
