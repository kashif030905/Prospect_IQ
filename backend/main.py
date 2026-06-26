from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.routes import procurement

# Create the FastAPI app instance
app = FastAPI(
    title="ProcureAI API",
    description="Agentic Procurement Intelligence Platform",
    version="1.0.0"
)

# CORS allows our Streamlit frontend to talk to this backend
# Without this, the browser blocks requests between different ports
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# Connect our procurement routes to the app
app.include_router(procurement.router, prefix="/api")

# Health check endpoint - confirms the server is running
@app.get("/")
def health_check():
    return {"status": "ProcureAI backend is running"}