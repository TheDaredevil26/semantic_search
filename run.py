"""
Run — Single entry point to start the Semantic Search on Alumni Graph system.
"""
import uvicorn
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import API_HOST, API_PORT

if __name__ == "__main__":
    print("\n>> Starting Semantic Search on Alumni Graph...")
    print(f"   Server: http://localhost:{API_PORT}")
    print(f"   API Docs: http://localhost:{API_PORT}/docs\n")

    uvicorn.run(
        "backend.main:app",
        host=API_HOST,
        port=API_PORT,
        reload=False,
        log_level="info",
    )
