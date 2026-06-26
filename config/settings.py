from dotenv import load_dotenv
import os

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Using Groq for now (free)
# Model: llama-3.3-70b is powerful and free on Groq
MODEL_NAME = "llama-3.3-70b-versatile"
APP_NAME = "ProcureAI"
APP_VERSION = "1.0.0"