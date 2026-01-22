#!/bin/bash
MODE=${MODE:-dev}
# Number of worker processes (default: 4 for production, adjust based on RAM)
# Each worker loads ~400MB GLiNER model, so 4 workers ≈ 1.6GB RAM for models
WORKERS=${WORKERS:-4}

# Suppress harmless warnings from ONNX Runtime and Transformers
export ONNXRUNTIME_DISABLE_CPUID_CHECK=1
export TOKENIZERS_PARALLELISM=false
export TRANSFORMERS_VERBOSITY=error

# Helper: ensure a command exists, else fail fast with a clear message
require_cmd() {
    if ! command -v "$1" >/dev/null 2>&1; then
        echo "Missing required command: $1" >&2
        echo "Container dependencies appear incomplete. Ensure requirements were installed during image build." >&2
        echo "Tip: Rebuild the image: docker-compose up --build -d (or docker build ...)" >&2
        exit 1
    fi
}

# Verify GLiNER is available (required for all modes)
python -c "import gliner" 2>/dev/null || {
    echo "GLiNER not available. Rebuild the image to install requirements." >&2
    exit 1
}

if [[ $MODE = dev ]]
then
    echo "Run container in dev mode"
    tail -f /dev/null
elif [[ $MODE = api ]]
then
    echo "Run container in api mode with $WORKERS workers"
    require_cmd uvicorn
    uvicorn anonymizer_api_app:anonymizer_api --host 0.0.0.0 --port 8000 --workers $WORKERS
elif [[ $MODE = web ]]
then
    echo "Run container in web mode with $WORKERS workers"
    require_cmd gunicorn
    python -c "import flask" 2>/dev/null || {
        echo "Flask not available. Rebuild the image to install requirements." >&2
        exit 1
    }
    gunicorn -w $WORKERS -b 0.0.0.0:8000 --timeout 600 anonymizer_flask_app:app
elif [[ $MODE = webapi ]]
then
    echo "Run container in web/api mode (single worker - mixing WSGI Flask with ASGI FastAPI)"
    require_cmd uvicorn
    # Note: Using single worker because:
    # 1. Flask app (WSGI) doesn't work well when forked with multiple uvicorn workers
    # 2. Both Flask and FastAPI initialize heavy resources (GLiNER model) at module load
    # 3. Each worker would try to load the 400MB model separately, causing OOM/crashes
    uvicorn anonymizer_api_webapp:main_app --host 0.0.0.0 --port 8000 --workers 1

else
    echo "unknown mode: "$MODE", use 'dev', 'api', 'web', 'webapi' or leave empty (defaults to 'dev')"
fi