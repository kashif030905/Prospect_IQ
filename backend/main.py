from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.routes import discovery
from backend.database import init_db

app = FastAPI(
    title="ProspectIQ API",
    description="Agentic AI Platform for B2B Customer Discovery",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

@app.on_event("startup")
def startup():
    init_db()

app.include_router(discovery.router, prefix="/api")

@app.get("/")
def health_check():
    return {"status": "ProspectIQ backend is running", "version": "2.0.0"}