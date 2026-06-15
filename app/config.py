import os
from pathlib import Path
from dotenv import load_dotenv
from Bio import Entrez

# Load environment variables
load_dotenv()

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent
EXPORTS_DIR = BASE_DIR / os.getenv("EXPORT_DIR", "exports")
DATA_DIR = BASE_DIR / "data"

# Create necessary directories
EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)

# NCBI Entrez Configuration
NCBI_EMAIL = os.getenv("NCBI_EMAIL", "default@example.com")
NCBI_API_KEY = os.getenv("NCBI_API_KEY", "")

Entrez.email = NCBI_EMAIL
if NCBI_API_KEY:
    Entrez.api_key = NCBI_API_KEY

# AI Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# App defaults
MAX_RESULTS_DEFAULT = int(os.getenv("MAX_RESULTS_DEFAULT", 20))