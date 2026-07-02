import pytest
from pathlib import Path
from tests.configtest import DOCS_PATH, cfg_ppt
from parsers.utils import common_utils as u1
from parsers.utils import ppt_utils as p
ext_list=[".pptx"]
DOCS_PATH=Path(DOCS_PATH)

@pytest.fixture(scope="module")
def load_initials():
    MD_DIR, PPT2PDF_DIR = p.load_saving_paths(cfg_ppt)
    docs = u1.list_docs( DOCS_PATH )
    docs_ppt = u1.filter_ext(docs, ext_list)
    return MD_DIR, PPT2PDF_DIR, docs_ppt

@pytest.fixture(scope="module")
def ppt2pdf(load_initials):
    MD_DIR, PPT2PDF_DIR, docs_ppt = load_initials
    ppt2pdf_docs=p.convert_ppt2pdf(docs_ppt, PPT2PDF_DIR)
    return ppt2pdf_docs

@pytest.fixture(scope="module")
def load_saved_raw_docling(load_initials):
    MD_DIR, PPT2PDF_DIR, docs_ppt = load_initials
    raw_md_list=u1.load_saved_obj(MD_DIR, 'raw_md_list.pkl')
    return raw_md_list


def test_load_initials(load_initials):
    MD_DIR, PPT2PDF_DIR, docs_ppt = load_initials
    assert len(docs_ppt)>0, f"data has no ppt file in {DOCS_PATH}"
    assert isinstance(DOCS_PATH, Path)
    assert isinstance(MD_DIR, Path)
    assert isinstance(PPT2PDF_DIR, Path)

def test_ppt2pdf(load_initials, ppt2pdf):
    MD_DIR, PPT2PDF_DIR, docs_ppt = load_initials
    ppt2pdf_docs=ppt2pdf
    assert len(ppt2pdf_docs)>0, f"data has no converted ppt to pdf file in {PPT2PDF_DIR}"

def test_save_raw_md(load_initials, ppt2pdf):
    MD_DIR, PPT2PDF_DIR, docs_ppt = load_initials
    ppt2pdf_docs=ppt2pdf
    if cfg_ppt.fresh_save_raw:
        raw_md_list = p.load_raw_docling(docs_ppt, ppt2pdf_docs)
        u1.save_obj(MD_DIR, 'raw_md_list.pkl', raw_md_list)
    # Assert it is not empty for next test of loading
    assert (MD_DIR/"raw_md_list.pkl").is_file(), f"no raw_md_list.pkl file saved in {MD_DIR}"

def test_load_saved_raw(load_saved_raw_docling):
    raw_md_list=load_saved_raw_docling  

def test_final(load_initials, load_saved_raw_docling):
    MD_DIR, PPT2PDF_DIR, docs_ppt = load_initials
    raw_md_list = load_saved_raw_docling
    ppt_md_list = raw_md_list
    if cfg_ppt.save_md:
        u1.save_obj(MD_DIR, 'ppt_md_list.pkl', ppt_md_list)
        u1.save_obj(MD_DIR, 'docs_ppt.pkl', docs_ppt)

    

        