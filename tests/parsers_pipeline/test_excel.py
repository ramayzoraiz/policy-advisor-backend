import pytest
from pathlib import Path
from tests.configtest import DOCS_PATH, cfg_excel
from parsers.utils import common_utils as u1
from parsers.utils import excel_utils as e
ext_list=[".xlsx"]
DOCS_PATH=Path(DOCS_PATH)

@pytest.fixture(scope="module")
def load_initials():
    MD_DIR = e.load_saving_paths(cfg_excel)
    docs = u1.list_docs(DOCS_PATH)
    docs_excel = u1.filter_ext(docs, ext_list)
    return MD_DIR, docs_excel

@pytest.fixture(scope="module")
def load_saved_raw_docling(load_initials):
    MD_DIR, docs_excel = load_initials
    raw_md_list=u1.load_saved_obj(MD_DIR, 'raw_md_list.pkl')
    return raw_md_list

@pytest.fixture(scope="module")
def table_gemini_correction(load_saved_raw_docling):
    raw_md_list = load_saved_raw_docling
    excel_md_list=e.table_correction(raw_md_list)
    return excel_md_list

def test_load_initials(load_initials):
    MD_DIR, docs_excel = load_initials
    assert len(docs_excel)>0, f"data has no excel file in {DOCS_PATH}"
    assert isinstance(DOCS_PATH, Path)
    assert isinstance(MD_DIR, Path)
    
def test_save_raw_md(load_initials):
    MD_DIR, docs_excel = load_initials
    if cfg_excel.fresh_save_raw:
        raw_md_list = e.load_raw_docling(docs_excel)
        u1.save_obj(MD_DIR, 'raw_md_list.pkl', raw_md_list)
    # Assert it is not empty for next test of loading
    assert (MD_DIR/"raw_md_list.pkl").is_file(), f"no raw_md_list.pkl file saved in {MD_DIR}"
    
def test_load_saved_raw_md(load_saved_raw_docling):
    raw_md_list=load_saved_raw_docling

def test_table_correction(load_initials, table_gemini_correction):
    MD_DIR, docs_excel = load_initials
    excel_md_list = table_gemini_correction
    if cfg_excel.save_md:
        u1.save_obj(MD_DIR, 'excel_md_list.pkl', excel_md_list)
        u1.save_obj(MD_DIR, 'docs_pdf.pkl', docs_excel)


    
