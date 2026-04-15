from dotenv import load_dotenv
from pathlib import Path
import os
load_dotenv(Path(__file__).resolve().parents[1] / ".env")
# BASE_DIR = Path(__file__).resolve().parent
# load_dotenv(BASE_DIR / ".env")

LOCAL_STORAGE_PATH = os.getenv("LOCAL_STORAGE_PATH", "./data")