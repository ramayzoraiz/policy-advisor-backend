import os
from dotenv import load_dotenv

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

from box import Box
cfg = Box.from_yaml(filename="./cfg.yaml")

DOCS_PATH = cfg.DOCS_DIR
PARSE_OUT = cfg.PARSE_OUT
SPLIT_OUT = cfg.SPLIT_OUT
VDB_OUT = cfg.VDB_OUT


cfg_pdf = cfg.PDF
cfg_excel = cfg.EXCEL
cfg_ppt = cfg.PPT
cfg_msword = cfg.MSWORD
cfg_image = cfg.IMAGE

cfg_split = cfg.SPLITTER

