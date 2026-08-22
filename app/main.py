from fastapi import FastAPI

from app.api.routes import router


app = FastAPI(
    title="CalQuity API",
    description="Enterprise AI Operations Assistant",
    version="1.0.0",
)


app.include_router(router)


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "CalQuity",
    }