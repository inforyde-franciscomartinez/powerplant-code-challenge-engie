import uvicorn
from fastapi import FastAPI

from application import api

app = FastAPI(
    title="Power Plant Challenge API",
)
if __name__ == "__main__":
    uvicorn.run(
        "application.main:app",
        host="0.0.0.0",
        port=8888,
        reload=True,
        log_level="info",
    )
