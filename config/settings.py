from dotenv import load_dotenv
import os

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

# llama-3.3-70b-versatile: better quality, 100k tokens/day on free tier
# llama-3.1-8b-instant: faster, 500k tokens/day — better for dev/testing
MODEL_NAME = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
APP_NAME = "ProcureAI"
APP_VERSION = "2.0.0"