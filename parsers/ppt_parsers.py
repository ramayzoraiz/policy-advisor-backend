from pathlib import Path
from parsers.utils import common_utils as u1
from parsers.utils import ppt_utils as p
from config import DOCS_PATH, cfg_ppt
ext_list=[".pptx"]
DOCS_PATH = Path(DOCS_PATH)

def pipeline1():
    MD_DIR, PPT2PDF_DIR = p.load_saving_paths(cfg_ppt)
    docs = u1.list_docs( DOCS_PATH )
    docs_ppt = u1.filter_ext(docs, ext_list)
    if cfg_ppt.return_saved:
        return docs_ppt, u1.load_saved_obj(MD_DIR, 'ppt_md_list.pkl')
    if cfg_ppt.fresh_save_raw:
        ppt2pdf_docs=p.convert_ppt2pdf(docs_ppt, PPT2PDF_DIR)
        raw_md_list=p.load_raw_docling(docs_ppt, ppt2pdf_docs)
        u1.save_obj(MD_DIR, 'raw_md_list.pkl', raw_md_list)
    raw_md_list=u1.load_saved_obj(MD_DIR, 'raw_md_list.pkl')
    # ppt_md_list=p.correction(raw_md_list)
    ppt_md_list=raw_md_list
    if cfg_ppt.save_md:
        u1.save_obj(MD_DIR, 'ppt_md_list.pkl', ppt_md_list)
    return docs_ppt, ppt_md_list

def pipeline2():
    pass
