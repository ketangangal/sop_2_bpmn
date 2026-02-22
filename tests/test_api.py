from io import BytesIO
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from src.main import app
from src.models.sop import (
    SOPBranch,
    SOPDecision,
    SOPDocument,
    SOPElement,
    SOPElementType,
)

client = TestClient(app)


class TestUIEndpoint:
    def test_ui_returns_html(self):
        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "SOP to BPMN Converter" in response.text
        assert "drop-zone" in response.text


class TestHealthEndpoint:
    def test_health_returns_200(self):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "sop-to-bpmn"


class TestConvertEndpoint:
    def test_rejects_non_docx(self):
        response = client.post(
            "/convert",
            files={"file": ("test.txt", b"some text", "text/plain")},
        )
        assert response.status_code == 400
        assert "Only .docx files" in response.json()["detail"]

    @patch("src.api.routes.get_parser")
    def test_convert_valid_docx(self, mock_get_parser, sample_sop_docx_bytes):
        """Test full pipeline with mocked LLM parser."""
        mock_parser = AsyncMock()
        mock_parser.parse.return_value = SOPDocument(
            title="Test SOP",
            elements=[
                SOPElement(element_type=SOPElementType.STEP, text="Step 1"),
                SOPElement(element_type=SOPElementType.STEP, text="Step 2"),
            ],
        )
        mock_get_parser.return_value = mock_parser

        response = client.post(
            "/convert",
            files={"file": ("test.docx", sample_sop_docx_bytes, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
        )

        assert response.status_code == 200
        assert "application/xml" in response.headers["content-type"]
        assert "test.bpmn" in response.headers.get("content-disposition", "")
        assert "<?xml" in response.text
        assert "startEvent" in response.text
        assert "endEvent" in response.text

    @patch("src.api.routes.get_parser")
    def test_convert_with_decision(self, mock_get_parser, sample_sop_docx_bytes):
        """Test pipeline with a decision in the SOP."""
        mock_parser = AsyncMock()
        mock_parser.parse.return_value = SOPDocument(
            title="Triage",
            elements=[
                SOPElement(element_type=SOPElementType.STEP, text="Receive email"),
                SOPElement(
                    element_type=SOPElementType.DECISION,
                    text="Check billing",
                    decision=SOPDecision(
                        question="Billing-related?",
                        branches=[
                            SOPBranch("Yes", [SOPElement(element_type=SOPElementType.STEP, text="Billing Queue")]),
                            SOPBranch("No", [SOPElement(element_type=SOPElementType.STEP, text="General Queue")]),
                        ],
                    ),
                ),
                SOPElement(element_type=SOPElementType.STEP, text="Send ack"),
            ],
        )
        mock_get_parser.return_value = mock_parser

        response = client.post(
            "/convert",
            files={"file": ("sop.docx", sample_sop_docx_bytes, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
        )

        assert response.status_code == 200
        assert "exclusiveGateway" in response.text
        assert "Billing Queue" in response.text
        assert "General Queue" in response.text
