# SOP to BPMN Converter

Converts Standard Operating Procedure (SOP) documents (`.docx`) into BPMN 2.0 XML files that can be visualized in [bpmn.io](https://bpmn.io). Uses **Azure OpenAI** (LLM) for intelligent SOP parsing and a **FastAPI** server with a web UI for the conversion.

---

## Table of Contents

- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Quick Start](#quick-start)
- [Setup Script](#setup-script)
- [Configuration](#configuration)
- [API Endpoints](#api-endpoints)
- [Web UI](#web-ui)
- [How It Works](#how-it-works)
- [Data Models](#data-models)
- [Module Reference](#module-reference)
- [Testing](#testing)
- [Examples](#examples)
- [Key Assumptions](#key-assumptions)
- [Current Scope & Limitations](#current-scope--limitations)
- [What I'd Improve With More Time](#what-id-improve-with-more-time)

---

## Architecture

```
  ┌───────────────────┐
  │  .docx SOP File   │
  └────────┬──────────┘
           │
           ▼
  ┌────────────────────┐
  │   DocxSOPParser    │  src/parser/docx_parser.py
  │  (python-docx)     │  Extracts raw paragraph text from .docx
  └────────┬───────────┘
           │
           ▼
  ┌────────────────────┐
  │  LLMSOPAnalyzer    │  src/parser/llm_analyzer.py
  │  (Azure OpenAI)    │  Sends text to GPT-4o with a structured prompt
  └────────┬───────────┘  Returns JSON → steps, decisions, branches
           │
           ▼
  ┌────────────────────┐
  │   SOPDocument      │  src/models/sop.py
  │  (Internal Model)  │  Python dataclasses — language-agnostic
  └────────┬───────────┘
           │
           ▼
  ┌────────────────────┐
  │   BPMNBuilder      │  src/generator/bpmn_builder.py
  │                    │  Walks SOP tree → creates BPMN graph
  └────────┬───────────┘  (nodes, gateways, sequence flows)
           │
           ▼
  ┌────────────────────┐
  │   LayoutEngine     │  src/generator/layout.py
  │                    │  Assigns x,y coordinates for rendering
  └────────┬───────────┘  Left-to-right, vertical branch fan-out
           │
           ▼
  ┌────────────────────┐
  │  BPMNXMLWriter     │  src/generator/bpmn_xml_writer.py
  │                    │  Serializes to BPMN 2.0 XML with
  └────────┬───────────┘  bpmn, bpmndi, dc, di namespaces
           │
           ▼
  ┌───────────────────┐
  │  .bpmn XML File   │  Viewable in bpmn.io
  └───────────────────┘
```

**Key design principle**: Each stage is a separate module with a clean interface. You can swap the parser (e.g., PDF instead of docx), improve the LLM prompt, change the layout algorithm, or alter the XML output — all independently.

---

## Project Structure

```
sop_2_bpmn/
├── setup.sh                    # One-command project setup
├── pyproject.toml              # Dependencies and project config
├── .env.example                # Environment variable template
├── README.md                   # This file
│
├── src/
│   ├── main.py                 # FastAPI application entry point
│   ├── config.py               # Settings (Azure OpenAI key, endpoint, deployment)
│   │
│   ├── models/                 # Data models (no business logic)
│   │   ├── sop.py              #   SOPDocument, SOPElement, SOPDecision, SOPBranch
│   │   └── bpmn.py             #   BPMNProcess, BPMNNode, BPMNSequenceFlow, Waypoint
│   │
│   ├── parser/                 # SOP document parsing
│   │   ├── base.py             #   Abstract BaseSOPParser interface
│   │   ├── docx_parser.py      #   .docx text extraction via python-docx
│   │   └── llm_analyzer.py     #   Azure OpenAI API call → structured SOPDocument
│   │
│   ├── generator/              # BPMN generation pipeline
│   │   ├── bpmn_builder.py     #   SOPDocument → BPMNProcess graph
│   │   ├── layout.py           #   Auto-layout coordinate assignment
│   │   └── bpmn_xml_writer.py  #   BPMNProcess → BPMN 2.0 XML string
│   │
│   ├── api/                    # HTTP layer
│   │   ├── routes.py           #   GET /, GET /health, POST /convert
│   │   └── dependencies.py     #   Dependency injection (parser, builder, writer)
│   │
│   └── templates/
│       └── index.html          # Web UI (drag & drop upload)
│
├── tests/                      # Test suite (26 tests)
│   ├── conftest.py             #   Shared fixtures
│   ├── test_parser.py          #   Docx text extraction tests
│   ├── test_bpmn_builder.py    #   Graph construction tests
│   ├── test_bpmn_xml_writer.py #   XML output tests
│   └── test_api.py             #   API endpoint + UI tests
│
├── examples/
│   ├── input_sop.docx          # Example SOP input
│   └── output.bpmn             # Generated BPMN output
│
└── problem_statement/
    └── Candidate Brief_Eng test.docx
```

---

## Quick Start

### Option 1: Automated setup

```bash
git clone <repo-url>
cd sop_2_bpmn
chmod +x setup.sh
./setup.sh
```

The script creates a venv, installs deps, sets up `.env`, and runs tests.

### Option 2: Manual setup

```bash
git clone <repo-url>
cd sop_2_bpmn

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -e ".[dev]"

# Configure Azure OpenAI
cp .env.example .env
# Edit .env → set AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT, etc.

# Run tests
pytest tests/ -v

# Start server
uvicorn src.main:app --reload
```

---

## Setup Script

`setup.sh` automates the full project setup:

| Step | What it does |
|------|-------------|
| 1 | Checks Python 3.11+ is installed |
| 2 | Creates `venv/` virtual environment (or reuses existing) |
| 3 | Upgrades pip, installs runtime + dev dependencies |
| 4 | Copies `.env.example` → `.env` (if not already present) |
| 5 | Runs the full test suite (26 tests) |
| 6 | Prints next-step instructions |

```bash
chmod +x setup.sh
./setup.sh
```

---

## Configuration

All configuration is via environment variables, loaded from a `.env` file by `pydantic-settings`.

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `AZURE_OPENAI_API_KEY` | Yes | — | Your Azure OpenAI API key |
| `AZURE_OPENAI_ENDPOINT` | Yes | — | Azure OpenAI resource endpoint (e.g. `https://your-resource.openai.azure.com`) |
| `AZURE_OPENAI_API_VERSION` | No | `2024-02-01` | Azure OpenAI API version |
| `AZURE_OPENAI_DEPLOYMENT` | No | `gpt-4o` | Azure OpenAI deployment name |

**Config file**: `src/config.py`

```python
class Settings(BaseSettings):
    azure_openai_api_key: str = ""
    azure_openai_endpoint: str = ""
    azure_openai_api_version: str = "2024-02-01"
    azure_openai_deployment: str = "gpt-4o"
    model_config = {"env_file": ".env", "extra": "ignore"}
```

---

## API Endpoints

| Method | Path | Description | Input | Output |
|--------|------|-------------|-------|--------|
| `GET` | `/` | Web UI — drag & drop upload page | — | HTML |
| `GET` | `/health` | Health check | — | `{"status": "healthy", "service": "sop-to-bpmn"}` |
| `POST` | `/convert` | Convert SOP to BPMN | Multipart `.docx` file | BPMN 2.0 XML (`application/xml`) |
| `GET` | `/docs` | Swagger UI (auto-generated) | — | HTML |
| `GET` | `/redoc` | ReDoc API docs (auto-generated) | — | HTML |

### POST /convert — Example

```bash
# Upload a .docx and save the BPMN output
curl -X POST http://localhost:8000/convert \
  -F "file=@examples/input_sop.docx" \
  -o output.bpmn
```

**Response headers:**
- `Content-Type: application/xml`
- `Content-Disposition: attachment; filename="input_sop.bpmn"`

**Error responses:**
- `400` — Non-`.docx` file uploaded or file read failure
- `422` — Conversion pipeline failed (LLM error, parsing error, etc.)

---

## Web UI

Open **http://localhost:8000** after starting the server.

**Features:**
- Drag & drop or click-to-browse `.docx` file upload
- File type validation (only `.docx` accepted)
- Animated pipeline progress indicator (Upload → Parse → LLM Analysis → Build BPMN → Generate XML)
- XML preview in a dark-themed code viewer
- One-click `.bpmn` file download
- Error messages for failed conversions

---

## How It Works

### Step 1: Text Extraction (`src/parser/docx_parser.py`)

`python-docx` reads the `.docx` binary and extracts all paragraph text, preserving line-by-line structure. Empty paragraphs are stripped.

```
Input:  .docx binary bytes
Output: Plain text string (one paragraph per line)
```

### Step 2: LLM Analysis (`src/parser/llm_analyzer.py`)

The extracted text is sent to **Azure OpenAI (GPT-4o)** with a structured system prompt. The prompt instructs the LLM to return a JSON object identifying:
- **Steps** — sequential actions
- **Decisions** — conditional checks with branches
- **Branches** — labeled paths (e.g., "Yes" / "No") each containing their own steps

The JSON response is parsed into `SOPDocument` dataclasses. Markdown code fences in the response are stripped automatically.

```
Input:  Plain text SOP
Output: SOPDocument (title + list of SOPElements)
```

### Step 3: BPMN Graph Construction (`src/generator/bpmn_builder.py`)

The `BPMNBuilder` walks the `SOPDocument` and creates a BPMN process graph:

- **Start Event** → first element
- **Steps** → `bpmn:task` nodes
- **Decisions** → diverging `exclusiveGateway` + branch tasks + converging `exclusiveGateway`
- **Last element** → **End Event**

Each decision produces a **gateway pair** (diverge + converge). Branches connect between them. The step *after* a decision connects to the converging gateway — this is how convergence is handled.

Nested decisions are supported recursively.

```
Input:  SOPDocument
Output: BPMNProcess (nodes + sequence flows)
```

### Step 4: Auto-Layout (`src/generator/layout.py`)

A left-to-right BFS layout assigns x,y coordinates:

- Sequential nodes advance by `HORIZONTAL_SPACING` (180px)
- Gateway branches fan out vertically by `VERTICAL_SPACING` (120px)
- Converging gateways wait for **all** incoming branches before being placed
- Waypoints on sequence flows use straight lines (same-y) or Z-shaped routing (different-y)

**Node dimensions:**

| Type | Width | Height |
|------|-------|--------|
| Start/End Event | 36 | 36 |
| Gateway | 50 | 50 |
| Task | 100 | 80 |

```
Input:  BPMNProcess (no coordinates)
Output: BPMNProcess (with x, y, waypoints)
```

### Step 5: XML Serialization (`src/generator/bpmn_xml_writer.py`)

Generates valid BPMN 2.0 XML with these namespaces (required by bpmn.io):

| Prefix | Namespace URI | Purpose |
|--------|--------------|---------|
| `bpmn` | `http://www.omg.org/spec/BPMN/20100524/MODEL` | Process elements |
| `bpmndi` | `http://www.omg.org/spec/BPMN/20100524/DI` | Diagram info |
| `dc` | `http://www.omg.org/spec/DD/20100524/DC` | Bounds (x, y, w, h) |
| `di` | `http://www.omg.org/spec/DD/20100524/DI` | Waypoints |

The XML contains two sections:
1. **`<bpmn:process>`** — nodes (startEvent, task, exclusiveGateway, endEvent) + sequenceFlows with incoming/outgoing references
2. **`<bpmndi:BPMNDiagram>`** — BPMNShape (with dc:Bounds) + BPMNEdge (with di:waypoint) for visual rendering

```
Input:  BPMNProcess (with layout)
Output: BPMN 2.0 XML string
```

---

## Data Models

### SOP Model (`src/models/sop.py`)

Represents the **parsed** SOP — completely decoupled from BPMN.

```
SOPDocument
├── title: str
└── elements: list[SOPElement]
                    ├── element_type: STEP | DECISION
                    ├── text: str
                    └── decision: SOPDecision (if DECISION)
                                  ├── question: str
                                  └── branches: list[SOPBranch]
                                                     ├── condition_label: str
                                                     └── steps: list[SOPElement]  ← recursive
```

### BPMN Model (`src/models/bpmn.py`)

Represents the **BPMN graph** ready for XML serialization.

```
BPMNProcess
├── id: str
├── name: str
├── nodes: list[BPMNNode]
│              ├── id, name: str
│              ├── node_type: START_EVENT | END_EVENT | TASK |
│              │              EXCLUSIVE_GATEWAY | CONVERGING_GATEWAY
│              └── x, y, width, height: float
└── sequence_flows: list[BPMNSequenceFlow]
                         ├── id, source_ref, target_ref, name: str
                         └── waypoints: list[Waypoint(x, y)]
```

---

## Module Reference

### `src/parser/base.py` — BaseSOPParser

Abstract base class. Implement this to add new input formats.

```python
class BaseSOPParser(ABC):
    async def parse(self, file_content: bytes) -> SOPDocument: ...
```

### `src/parser/docx_parser.py` — DocxSOPParser

Extracts text from `.docx` using `python-docx`, then delegates to `LLMSOPAnalyzer`.

### `src/parser/llm_analyzer.py` — LLMSOPAnalyzer

Calls Azure OpenAI API with a structured prompt. The prompt defines the exact JSON schema the LLM should return. Handles markdown fence stripping and recursive JSON → dataclass parsing.

### `src/generator/bpmn_builder.py` — BPMNBuilder

Converts `SOPDocument` → `BPMNProcess`. Creates unique IDs for all nodes/flows. Handles decisions by creating diverging + converging gateway pairs with branch tasks between them.

### `src/generator/layout.py` — LayoutEngine

BFS-based left-to-right layout. Positions nodes, computes waypoints. Handles gateway fan-out/fan-in with vertical spacing.

### `src/generator/bpmn_xml_writer.py` — BPMNXMLWriter

Uses `xml.etree.ElementTree` (stdlib) to build the XML tree. Outputs BPMN 2.0 with all four required namespaces plus the BPMNDiagram section.

### `src/api/dependencies.py` — Dependency Injection

Single place to swap implementations. Change the parser, builder, layout engine, or XML writer here.

```python
def get_parser() -> DocxSOPParser:       # swap to PDFSOPParser, etc.
def get_builder() -> BPMNBuilder:
def get_layout_engine() -> LayoutEngine:
def get_xml_writer() -> BPMNXMLWriter:
```

---

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run a specific test file
pytest tests/test_bpmn_builder.py -v

# Run with output
pytest tests/ -v -s
```

### Test Coverage (26 tests)

| File | Tests | What's covered |
|------|-------|----------------|
| `test_api.py` | 5 | UI endpoint, health check, file validation, full pipeline (mocked LLM), decision pipeline |
| `test_bpmn_builder.py` | 5 | Linear process, gateway creation, node count, ID uniqueness, flow label validation, ref validation |
| `test_bpmn_xml_writer.py` | 9 | Well-formed XML, namespaces, process element, diagram section, events, gateways, flow refs, linear XML, bounds |
| `test_parser.py` | 3 | Text extraction, empty doc, line structure preservation |
| `conftest.py` | — | Shared fixtures: sample docx bytes, sample SOPDocument, linear SOPDocument |

**Note:** LLM calls are **mocked** in API tests — no API key needed to run tests.

---

## Examples

### Input: `examples/input_sop.docx`

```
Customer Support Email Triage

1. Receive customer support email.
2. Check if the issue is billing-related.
   If yes, assign to Billing Queue.
   If no, assign to General Support Queue.
3. Send acknowledgment email to customer.
4. Close the triage step.
```

### Output: `examples/output.bpmn`

The generated BPMN produces this flow when opened in bpmn.io:

```
[Start] → [Receive email] → <Billing-related?> ──Yes──→ [Assign to Billing Queue] ──┐
                                    │                                                  │
                                    └──No──→ [Assign to General Support Queue] ────────┘
                                                                                       │
                                                                              <Converge Gateway>
                                                                                       │
                                                        [Send acknowledgment] ← ───────┘
                                                                │
                                                        [Close triage step]
                                                                │
                                                             [End]
```

To visualize: open `examples/output.bpmn` at [demo.bpmn.io](https://demo.bpmn.io/).

---

## Key Assumptions

1. **Input format** — The SOP is a `.docx` file with readable paragraph text (not scanned images or tables-only).
2. **LLM parsing** — The LLM (GPT-4o) handles varied SOP styles. It does not require strict numbering, specific keywords, or rigid formatting.
3. **Decision convergence** — Branches from a decision converge back into the main flow at the next sequential step after the decision block.
4. **Nesting** — Nested decisions (a decision inside a branch) are supported by the data model and builder recursively.
5. **Two+ branches** — Decisions can have more than two branches (not limited to yes/no).
6. **Sequential flow** — The overall SOP is a single sequential flow with decisions. Parallel execution is not detected.

---

## Current Scope & Limitations

### What we handle

| SOP Pattern | BPMN Element |
|-------------|-------------|
| Sequential steps | `bpmn:task` |
| If/then decisions | `bpmn:exclusiveGateway` (diverge + converge) |
| Yes/No/custom branches | Labeled `bpmn:sequenceFlow` |
| Nested decisions | Recursive gateway pairs |

### What we don't handle (yet)

| Pattern | BPMN Element | Why |
|---------|-------------|-----|
| Parallel actions ("do A and B at the same time") | Parallel Gateway (AND) | Not detected by current LLM prompt |
| Loops ("repeat until approved") | Loop-back sequence flow | Requires cycle detection in builder |
| Roles/departments | Swimlanes / Pools | No role extraction in parser |
| Timers ("wait 48 hours") | Timer Events | Not in current BPMN model |
| Sub-procedures | Sub-processes | Not in current BPMN model |
| Error handling | Error Events | Not in current BPMN model |
| PDF / plain text input | — | Only `.docx` parser implemented |

---

## What I'd Improve With More Time

1. **PDF and plain-text support** — Add `PDFSOPParser` implementing `BaseSOPParser`. Only `dependencies.py` changes.
2. **Parallel gateway detection** — Update LLM prompt to detect "while/simultaneously/at the same time" patterns. Add `PARALLEL_GATEWAY` to `BPMNNodeType`.
3. **Loop detection** — Teach the LLM to detect "go back to step X" and generate loop-back flows.
4. **Swimlanes** — Add a `role` field to `SOPElement`, generate `<bpmn:laneSet>` in XML writer.
5. **Sugiyama layout** — Replace simple BFS layout with a proper layered graph layout algorithm for complex processes.
6. **BPMN XSD validation** — Validate generated XML against the official BPMN 2.0 schema before returning.
7. **Streaming responses** — Use the LLM's streaming API for real-time progress during analysis.
8. **Caching** — Cache LLM responses for identical SOP inputs to reduce API calls and latency.
9. **Error recovery** — Retry logic with exponential backoff; fallback to regex-based parsing if LLM fails.
10. **Export formats** — Add SVG/PNG export using a headless bpmn.io renderer.

---

## Dependencies

### Runtime

| Package | Version | Purpose |
|---------|---------|---------|
| `fastapi` | >=0.104.0 | Web framework (API + serves UI) |
| `uvicorn[standard]` | >=0.24.0 | ASGI server (uvloop + httptools) |
| `python-docx` | >=1.1.0 | Read `.docx` files |
| `python-multipart` | >=0.0.6 | File upload support for FastAPI |
| `openai` | >=1.0.0 | Azure OpenAI API client |
| `pydantic-settings` | >=2.0.0 | Load settings from `.env` |

### Dev

| Package | Version | Purpose |
|---------|---------|---------|
| `pytest` | >=7.4.0 | Test runner |
| `pytest-asyncio` | >=0.23.0 | Async test support |
| `httpx` | >=0.25.0 | Required by FastAPI TestClient |

---

## License

This project was built as an engineering exercise.
