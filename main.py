from fastapi import FastAPI

from app.api.routes import router


app = FastAPI(
    title="CalQuity AI",
    description="AI-powered customer support agent for ParcelPilot",
    version="1.0.0",
)

app.include_router(router)


@app.get("/")
def root():
    return {
        "message": "CalQuity AI is running",
        "status": "ok",
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }