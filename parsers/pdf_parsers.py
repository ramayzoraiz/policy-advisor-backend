from pathlib import Path
from parsers.utils import common_utils as u1
from parsers.utils import pdf_utils as p
from config import DOCS_PATH, cfg_pdf
ext_list=[".pdf"]

def pipeline1():
    MD_DIR, MD_PYMUPDF_DIR, MD_DOCLING_DIR = p.load_saving_paths(cfg_pdf)
    docs = u1.list_docs( Path(DOCS_PATH) )
    docs_pdf = u1.filter_ext(docs, ext_list)
    if cfg_pdf.return_saved:
        return docs_pdf, p.load_saved(MD_DIR)
    
    if cfg_pdf.fresh_save_raw:
        p.save_raw_md_from_pdf(docs_pdf, MD_PYMUPDF_DIR, MD_DOCLING_DIR)
    pymupdf_md_list, docling_md_list=p.load_saved_raw_md_from_pdf(MD_PYMUPDF_DIR, MD_DOCLING_DIR)
    docling_pages_md_list = p.docling_md_splitting(docling_md_list, pymupdf_md_list)
    docling_pages_md_list = p.mismatch_pages_correction(docs_pdf, docling_pages_md_list, pymupdf_md_list)
    md_list = p.modify_langpages(docling_pages_md_list, pymupdf_md_list)
    md_list = p.place_empty_string_for_non_word_pgs(md_list)
    if cfg_pdf.save_md:
        p.save_md(MD_DIR, md_list)
    return docs_pdf, md_list

def pipeline1():
    MD_DIR, MD_PYMUPDF_DIR, MD_DOCLING_DIR = p.load_saving_paths(cfg_pdf)
    docs = u1.list_docs( Path(DOCS_PATH) )
    docs_pdf = u1.filter_ext(docs, ext_list)
    if cfg_pdf.return_saved:
        return docs_pdf, p.load_saved(MD_DIR)
    
    if cfg_pdf.fresh_save_raw:
        p.save_raw_md_from_pdf(docs_pdf, MD_PYMUPDF_DIR, MD_DOCLING_DIR)
    pymupdf_md_list, docling_md_list=p.load_saved_raw_md_from_pdf(MD_PYMUPDF_DIR, MD_DOCLING_DIR)
    docling_pages_md_list = p.docling_md_splitting(docling_md_list, pymupdf_md_list)
    
    p.num_of_pages_mismatch(docling_pages_md_list, pymupdf_md_list, MD_DIR)
    docling_pages_md_list = p.blank_docs_correction_for_mismatched(docs_pdf, docling_pages_md_list, MD_DIR)

    docling_pages_md_list = p.mismatch_pages_alignment_correction(docs_pdf, docling_pages_md_list, pymupdf_md_list, MD_DIR)
    md_list = p.modify_langpages(docling_pages_md_list, pymupdf_md_list)
    md_list = p.place_empty_string_for_non_word_pgs(md_list)
    if cfg_pdf.save_md:
        p.save_md(MD_DIR, md_list)
    return docs_pdf, md_list

def pipeline2():
    pass
