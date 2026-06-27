from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.routes import discovery

app = FastAPI(
    title="ProcureAI API",
    description="Reusable Agentic AI Platform for Customer Discovery",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

app.include_router(discovery.router, prefix="/api")

@app.get("/")
def health_check():
    return {"status": "ProcureAI backend is running", "version": "2.0.0"}