from pathlib import Path
from parsers.utils import common_utils as u1
from parsers.utils import msword_utils as p
from copy import deepcopy
from config import DOCS_PATH, cfg_msword
ext_list=[".doc",".docx"] #4,15
DOCS_PATH = Path(DOCS_PATH)

def pipeline1():
    MD_DIR, MSWORD2DOCX_DIR, MSWORD2PDF_DIR = p.load_saving_paths(cfg_msword)
    docs = u1.list_docs( DOCS_PATH )
    docs_msword = u1.filter_ext(docs, ext_list)
    # flatten out nested list of .doc and .docx into one
    fdocs_msword = docs_msword
    if isinstance(docs_msword[0], list):
        fdocs_msword = [doc_path for docs_sublist in docs_msword for doc_path in docs_sublist]
    
    if cfg_msword.return_saved:
        return fdocs_msword, u1.load_saved_obj(MD_DIR, 'msword_md_list.pkl')
    if cfg_msword.fresh_save_raw:
        p.save_raw_parse(fdocs_msword, MSWORD2DOCX_DIR, MSWORD2PDF_DIR)
    docx_raw_list, pdf_raw_list=p.load_saved_raw_parse(MSWORD2DOCX_DIR, MSWORD2PDF_DIR)
        
    msword_md_list = p.finalize(docx_raw_list, pdf_raw_list)
    if cfg_msword.save_md:
        u1.save_obj(MD_DIR, 'msword_md_list.pkl', msword_md_list)
    return fdocs_msword, msword_md_list

def pipeline2():
    """disregard docx and just parse converted pdfs"""
    MD_DIR, _, MSWORD2PDF_DIR = p.load_saving_paths(cfg_msword)
    docs = u1.list_docs( DOCS_PATH )
    docs_msword = u1.filter_ext(docs, ext_list)
    # flatten out nested list of .doc and .docx into one
    fdocs_msword = docs_msword
    if isinstance(docs_msword[0], list):
        fdocs_msword = [doc_path for docs_sublist in docs_msword for doc_path in docs_sublist]
    
    if cfg_msword.return_saved:
        return fdocs_msword, u1.load_saved_obj(MD_DIR, 'msword_md_list.pkl')
    if cfg_msword.fresh_save_raw:
        msword2pdf_docs = p.convert_msword2pdf(fdocs_msword, MSWORD2PDF_DIR)
        pdf_raw_list = p.load_raw_pdf_docling(fdocs_msword, msword2pdf_docs)
        u1.save_obj(MSWORD2PDF_DIR, 'raw.pkl', pdf_raw_list)
    pdf_raw_list = u1.load_saved_obj(MSWORD2PDF_DIR, 'raw.pkl')
    
    msword_md_list = pdf_raw_list 
    if cfg_msword.save_md:
        u1.save_obj(MD_DIR, 'msword_md_list.pkl', msword_md_list)
    return fdocs_msword, msword_md_list
