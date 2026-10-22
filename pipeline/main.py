"""
main.py — Root alias entrypoint for Flashcard AI Pipeline (FastAPI)
"""

import os
import sys
from pathlib import Path
import uvicorn

_PIPELINE_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _PIPELINE_DIR.parent

for _p in [str(_PROJECT_ROOT), str(_PIPELINE_DIR)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    app_target = (
        "pipeline.app.main:app"
        if (_PROJECT_ROOT / "pipeline").exists()
        else "app.main:app"
    )
    uvicorn.run(app_target, host=host, port=port, reload=True)
