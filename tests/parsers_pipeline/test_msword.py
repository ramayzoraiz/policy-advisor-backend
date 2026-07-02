import pytest
from pathlib import Path
from tests.configtest import DOCS_PATH, cfg_msword
from parsers.utils import common_utils as u1
from parsers.utils import msword_utils as p
ext_list=[".doc",".docx"]
DOCS_PATH=Path(DOCS_PATH)

@pytest.fixture(scope="module")
def load_initials():
    MD_DIR, MSWORD2DOCX_DIR, MSWORD2PDF_DIR = p.load_saving_paths(cfg_msword)
    docs = u1.list_docs( DOCS_PATH )
    docs_msword = u1.filter_ext(docs, ext_list)
    # flatten out nested list of .doc and .docx into one
    fdocs_msword = docs_msword
    if isinstance(docs_msword[0], list):
        fdocs_msword = [doc_path for docs_sublist in docs_msword for doc_path in docs_sublist]
    return MD_DIR, MSWORD2DOCX_DIR, MSWORD2PDF_DIR, fdocs_msword

@pytest.fixture(scope="module")
def load_saved_raw_parse(load_initials):
    MD_DIR, MSWORD2DOCX_DIR, MSWORD2PDF_DIR, fdocs_msword = load_initials
    docx_raw_list, pdf_raw_list=p.load_saved_raw_parse(MSWORD2DOCX_DIR, MSWORD2PDF_DIR)
    return docx_raw_list, pdf_raw_list


def test_load_initials(load_initials):
    MD_DIR, MSWORD2DOCX_DIR, MSWORD2PDF_DIR, fdocs_msword = load_initials
    assert len(fdocs_msword)>0, f"data has no msword file in {DOCS_PATH}"
    assert isinstance(DOCS_PATH, Path)
    assert isinstance(MD_DIR, Path)
    assert isinstance(MSWORD2DOCX_DIR, Path)
    assert isinstance(MSWORD2PDF_DIR, Path)

def test_save_raw_parse(load_initials):
    MD_DIR, MSWORD2DOCX_DIR, MSWORD2PDF_DIR, fdocs_msword = load_initials
    if cfg_msword.fresh_save_raw:
        # p.save_raw_parse(fdocs_msword, MSWORD2DOCX_DIR, MSWORD2PDF_DIR)
        docs_docx = p.convert_msword2docx(fdocs_msword, MSWORD2DOCX_DIR)
        docx_raw_list = p.load_raw_docx_docling(fdocs_msword, docs_docx)
        u1.save_obj(MSWORD2DOCX_DIR, 'raw.pkl', docx_raw_list)
        msword2pdf_docs = p.convert_msword2pdf(fdocs_msword, MSWORD2PDF_DIR)
        pdf_raw_list = p.load_raw_pdf_docling(fdocs_msword, msword2pdf_docs)
        u1.save_obj(MSWORD2PDF_DIR, 'raw.pkl', pdf_raw_list)

    # Assert it is not empty for next test of loading
    assert len(docs_docx)>0, f"data has no converted msword to docx file in {MSWORD2DOCX_DIR}"
    assert len(msword2pdf_docs)>0, f"data has no converted msword to pdf file in {MSWORD2PDF_DIR}"
    assert (MSWORD2DOCX_DIR/"raw.pkl").is_file(), f"no raw.pkl file saved in {MSWORD2DOCX_DIR}"
    assert (MSWORD2PDF_DIR/"raw.pkl").is_file(), f"no raw.pkl file saved in {MSWORD2PDF_DIR}"  

def test_final(load_initials, load_saved_raw_parse):
    MD_DIR, MSWORD2DOCX_DIR, MSWORD2PDF_DIR, fdocs_msword = load_initials
    docx_raw_list, pdf_raw_list = load_saved_raw_parse
    msword_md_list = p.finalize(docx_raw_list, pdf_raw_list)
    if cfg_msword.save_md:
        u1.save_obj(MD_DIR, 'msword_md_list.pkl', msword_md_list)
        u1.save_obj(MD_DIR, 'docs_msword.pkl', fdocs_msword)
    

