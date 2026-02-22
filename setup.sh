#!/usr/bin/env bash
set -euo pipefail

# ============================================================
#  SOP to BPMN Converter — Project Setup
# ============================================================
#  Usage:
#    chmod +x setup.sh
#    ./setup.sh
#
#  What this script does:
#    1. Checks prerequisites (Python 3.11+)
#    2. Creates a virtual environment
#    3. Installs project dependencies (runtime + dev)
#    4. Sets up .env file from template
#    5. Runs the test suite to verify everything works
#    6. Prints next-step instructions
# ============================================================

PYTHON_MIN_VERSION="3.11"
VENV_DIR="venv"
ENV_FILE=".env"
ENV_EXAMPLE=".env.example"

# --- Colors ---
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

info()    { echo -e "${BLUE}[INFO]${NC}  $1"; }
success() { echo -e "${GREEN}[OK]${NC}    $1"; }
warn()    { echo -e "${YELLOW}[WARN]${NC}  $1"; }
error()   { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

echo ""
echo "=========================================="
echo "  SOP to BPMN Converter — Setup"
echo "=========================================="
echo ""

# ----------------------------------------------------------
# 1. Check Python version
# ----------------------------------------------------------
info "Checking Python installation..."

if command -v python3 &>/dev/null; then
    PYTHON_CMD="python3"
elif command -v python &>/dev/null; then
    PYTHON_CMD="python"
else
    error "Python is not installed. Please install Python ${PYTHON_MIN_VERSION}+ and try again."
fi

PYTHON_VERSION=$($PYTHON_CMD -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
PYTHON_MAJOR=$($PYTHON_CMD -c "import sys; print(sys.version_info.major)")
PYTHON_MINOR=$($PYTHON_CMD -c "import sys; print(sys.version_info.minor)")

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 11 ]); then
    error "Python ${PYTHON_MIN_VERSION}+ is required. Found: Python ${PYTHON_VERSION}"
fi

success "Python ${PYTHON_VERSION} found (${PYTHON_CMD})"

# ----------------------------------------------------------
# 2. Create virtual environment
# ----------------------------------------------------------
if [ -d "$VENV_DIR" ]; then
    warn "Virtual environment '${VENV_DIR}/' already exists. Reusing it."
else
    info "Creating virtual environment..."
    $PYTHON_CMD -m venv "$VENV_DIR"
    success "Virtual environment created at ${VENV_DIR}/"
fi

# Activate venv
# shellcheck disable=SC1091
source "${VENV_DIR}/bin/activate"
success "Virtual environment activated"

# ----------------------------------------------------------
# 3. Upgrade pip and install dependencies
# ----------------------------------------------------------
info "Upgrading pip..."
pip install --upgrade pip --quiet

info "Installing project dependencies (runtime + dev)..."
pip install -e ".[dev]" --quiet
success "All dependencies installed"

# ----------------------------------------------------------
# 4. Set up .env file
# ----------------------------------------------------------
if [ -f "$ENV_FILE" ]; then
    warn ".env file already exists. Skipping creation."
else
    if [ -f "$ENV_EXAMPLE" ]; then
        cp "$ENV_EXAMPLE" "$ENV_FILE"
        success ".env file created from ${ENV_EXAMPLE}"
        warn "Please edit .env and add your Azure OpenAI credentials before running the server."
    else
        warn ".env.example not found. Creating a blank .env file."
        cat > "$ENV_FILE" <<EOL
AZURE_OPENAI_API_KEY=your-api-key-here
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com
AZURE_OPENAI_API_VERSION=2024-02-01
AZURE_OPENAI_DEPLOYMENT=gpt-4o
EOL
        warn "Please edit .env and add your Azure OpenAI credentials before running the server."
    fi
fi

# ----------------------------------------------------------
# 5. Run tests
# ----------------------------------------------------------
echo ""
info "Running test suite..."
echo ""

if pytest tests/ -v; then
    echo ""
    success "All tests passed!"
else
    echo ""
    warn "Some tests failed. Check the output above for details."
fi

# ----------------------------------------------------------
# 6. Done — Print instructions
# ----------------------------------------------------------
echo ""
echo "=========================================="
echo -e "  ${GREEN}Setup Complete!${NC}"
echo "=========================================="
echo ""
echo "  Next steps:"
echo ""
echo "  1. Add your API key:"
echo -e "     ${YELLOW}Edit .env and set your Azure OpenAI credentials${NC}"
echo ""
echo "  2. Start the server:"
echo -e "     ${BLUE}source venv/bin/activate${NC}"
echo -e "     ${BLUE}uvicorn src.main:app --reload${NC}"
echo ""
echo "  3. Open the UI:"
echo -e "     ${BLUE}http://localhost:8000${NC}"
echo ""
echo "  4. Or use the API directly:"
echo -e "     ${BLUE}curl -X POST http://localhost:8000/convert \\${NC}"
echo -e "     ${BLUE}  -F \"file=@examples/input_sop.docx\" \\${NC}"
echo -e "     ${BLUE}  -o output.bpmn${NC}"
echo ""
echo "  5. Run tests anytime:"
echo -e "     ${BLUE}pytest tests/ -v${NC}"
echo ""
echo "  6. API docs (Swagger UI):"
echo -e "     ${BLUE}http://localhost:8000/docs${NC}"
echo ""
