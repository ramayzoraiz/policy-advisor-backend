import os
from dotenv import load_dotenv

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

from box import Box
cfg = Box.from_yaml(filename="./cfg.yaml")

DOCS_PATH = cfg.DOCS_DIR
cfg_pdf = cfg.PDF
cfg_excel = cfg.EXCEL

