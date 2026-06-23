from parsers.utils import excel_utils as e
from parsers.utils import common_utils as u1
from pathlib import Path
from config import DOCS_PATH, cfg_excel
ext_list=[".xlsx"]
DOCS_PATH = Path(DOCS_PATH)

def pipeline1():
    MD_DIR = e.load_saving_paths(cfg_excel)
    docs = u1.list_docs( DOCS_PATH )
    docs_excel = u1.filter_ext(docs, ext_list)
    if cfg_excel.return_saved:
        return docs_excel, u1.load_saved_obj(MD_DIR, 'excel_md_list.pkl')
    if cfg_excel.fresh_save_raw:
        raw_md_list=e.load_raw_docling(docs_excel)
        u1.save_obj(MD_DIR, 'raw_md_list.pkl', raw_md_list)
    raw_md_list=u1.load_saved_obj(MD_DIR, 'raw_md_list.pkl')
    excel_md_list=e.table_correction(raw_md_list)
    if cfg_excel.save_md:
        u1.save_obj(MD_DIR, 'excel_md_list.pkl', excel_md_list)
    return docs_excel, excel_md_list

def pipeline2():
    pass


