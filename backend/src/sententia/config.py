import os

from dotenv import load_dotenv

load_dotenv()

MAX_ATTEMPTS = 3

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")  # unused until phase 3/4
CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./chroma_data")  # unused until phase 2
