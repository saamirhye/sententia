import os

from dotenv import load_dotenv

load_dotenv()

MAX_ATTEMPTS = 3

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")  # used by assess() and generate()
ANTHROPIC_MODEL_ASSESS = os.getenv("ANTHROPIC_MODEL_ASSESS", "claude-haiku-4-5-20251001")
ANTHROPIC_MODEL_GENERATE = os.getenv("ANTHROPIC_MODEL_GENERATE", "claude-sonnet-5")
CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./chroma_data")
