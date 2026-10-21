"""
main.py — Root alias entrypoint for pipeline/app/main.py
Enables running `python main.py` directly from inside pipeline/
"""

import os
import uvicorn
from app.main import app

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    uvicorn.run("app.main:app", host=host, port=port, reload=True)

