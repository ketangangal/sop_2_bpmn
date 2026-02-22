import logging

from fastapi import FastAPI

from src.api.routes import router

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")

app = FastAPI(
    title="SOP to BPMN Converter",
    description="Converts Standard Operating Procedure documents (.docx) to BPMN 2.0 XML using LLM-powered analysis",
    version="1.0.0",
)

app.include_router(router)
