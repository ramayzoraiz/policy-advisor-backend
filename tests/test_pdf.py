import pytest
from pathlib import Path
from tests.configtest import DOCS_PATH, cfg_pdf
from parsers.utils import common_utils as u1
from parsers.utils import pdf_utils as p
ext_list=[".pdf"]
DOCS_PATH=Path(DOCS_PATH)

@pytest.fixture(scope="module")
def load_initials():
    MD_DIR, MD_PYMUPDF_DIR, MD_DOCLING_DIR = p.load_saving_paths(cfg_pdf)
    docs = u1.list_docs(DOCS_PATH)
    docs_pdf = u1.filter_ext(docs, ext_list)
    return MD_DIR, MD_PYMUPDF_DIR, MD_DOCLING_DIR, docs_pdf

@pytest.fixture(scope="module")
def load_raw_md(load_initials):
    MD_DIR, MD_PYMUPDF_DIR, MD_DOCLING_DIR, docs_pdf = load_initials
    pymupdf_md_list, docling_md_list=p.load_saved_raw_md_from_pdf(MD_PYMUPDF_DIR, MD_DOCLING_DIR)
    p.view_save(DOCS_PATH, docs_pdf, MD_PYMUPDF_DIR, MD_DOCLING_DIR)
    return pymupdf_md_list, docling_md_list

@pytest.fixture(scope="module")
def docling_md_splitting(load_raw_md):
    pymupdf_md_list, docling_md_list = load_raw_md
    docling_pages_md_list = p.docling_split_single_md_to_pages_md(docling_md_list)
    return docling_pages_md_list

@pytest.fixture(scope="module")
def indices_mismatch_blank_docs(load_initials, docling_md_splitting):
    MD_DIR, MD_PYMUPDF_DIR, MD_DOCLING_DIR, docs_pdf = load_initials
    docling_pages_md_list = docling_md_splitting
    # read mismatch index
    if not (MD_DIR/"log_mismatch_index.txt").exists():
        return [], []
    with open(MD_DIR/"log_mismatch_index.txt", 'r') as file:
        mismatch_docs_indices = [int(line.strip()) for line in file]
    empty_mismatch_docs_indices=p.identify_indices_of_blank_docs(mismatch_docs_indices, docling_pages_md_list)
    return mismatch_docs_indices, empty_mismatch_docs_indices

@pytest.fixture(scope="module")
def redocling(load_initials, docling_md_splitting, indices_mismatch_blank_docs):
    MD_DIR, MD_PYMUPDF_DIR, MD_DOCLING_DIR, docs_pdf = load_initials
    docling_pages_md_list = docling_md_splitting
    mismatch_docs_indices, empty_mismatch_docs_indices = indices_mismatch_blank_docs
    docling_pages_md_list=p.docling_reload_and_resplit(empty_mismatch_docs_indices, docs_pdf, docling_pages_md_list)
    return docling_pages_md_list

@pytest.fixture(scope="module")
def punctuation_gemini(indices_mismatch_blank_docs, redocling):
    docling_pages_md_list = redocling
    mismatch_docs_indices, empty_mismatch_docs_indices = indices_mismatch_blank_docs
    docling_pages_md_list=p.punctuation_correction(empty_mismatch_docs_indices, docling_pages_md_list)
    return docling_pages_md_list

@pytest.fixture(scope="module")
def alignment_correction(load_initials, load_raw_md, indices_mismatch_blank_docs, docling_md_splitting, punctuation_gemini):
    MD_DIR, MD_PYMUPDF_DIR, MD_DOCLING_DIR, docs_pdf = load_initials
    pymupdf_md_list, docling_md_list = load_raw_md
    mismatch_docs_indices, empty_mismatch_docs_indices = indices_mismatch_blank_docs

    docling_pages_md_list = docling_md_splitting
    if len(mismatch_docs_indices)==0:
        print("alignment correction executed as no pdf docs has mismatch pages")
        return docling_pages_md_list
    
    if len(empty_mismatch_docs_indices)>0:
        docling_pages_md_list = punctuation_gemini
    docling_pages_md_list=p.mismatch_pages_alignment_correction(docs_pdf, docling_pages_md_list,
                            pymupdf_md_list, MD_DIR)
    return docling_pages_md_list

@pytest.fixture(scope="module")
def modify_langpages(load_raw_md, alignment_correction):
    pymupdf_md_list, docling_md_list = load_raw_md
    docling_pages_md_list = alignment_correction
    md_list=p.modify_langpages(docling_pages_md_list, pymupdf_md_list)
    return md_list


def test_load_initials(load_initials):
    MD_DIR, MD_PYMUPDF_DIR, MD_DOCLING_DIR, docs_pdf = load_initials
    assert len(docs_pdf)>0, f"data has no pdf file in {DOCS_PATH}"
    assert isinstance(DOCS_PATH, Path)
    assert isinstance(MD_DIR, Path)
    assert isinstance(MD_PYMUPDF_DIR, Path)
    assert isinstance(MD_DOCLING_DIR, Path)


def test_save_raw_md(load_initials):
    MD_DIR, MD_PYMUPDF_DIR, MD_DOCLING_DIR, docs_pdf = load_initials
    if cfg_pdf.fresh_save_raw:
        p.save_raw_md_from_pdf(docs_pdf, MD_PYMUPDF_DIR, MD_DOCLING_DIR)
    # Assert it is not empty for next test of loading
    assert (MD_PYMUPDF_DIR/"raw.pkl").is_file(), f"no raw.pkl file saved in {MD_PYMUPDF_DIR}"
    assert (MD_DOCLING_DIR/"raw.pkl").is_file(), f"no raw.pkl file saved in {MD_DOCLING_DIR}"
    

def test_load_saved_raw_md_from_pdf(load_initials, load_raw_md):
    MD_DIR, MD_PYMUPDF_DIR, MD_DOCLING_DIR, docs_pdf = load_initials
    pymupdf_md_list, docling_md_list=load_raw_md
    p.view_save(DOCS_PATH, docs_pdf, MD_PYMUPDF_DIR, MD_DOCLING_DIR)
    

def test_docling_md_splitting(load_initials, docling_md_splitting):
    MD_DIR, MD_PYMUPDF_DIR, MD_DOCLING_DIR, docs_pdf = load_initials
    docling_pages_md_list = docling_md_splitting
    u1.save_obj(MD_DOCLING_DIR, 'pages_raw.pkl', docling_pages_md_list)
    

def test_docs_with_diff_num_of_pgs(load_initials, load_raw_md, docling_md_splitting):
    MD_DIR, MD_PYMUPDF_DIR, MD_DOCLING_DIR, docs_pdf = load_initials
    pymupdf_md_list, docling_md_list = load_raw_md
    docling_pages_md_list = docling_md_splitting
    p.num_of_pages_mismatch(docling_pages_md_list, pymupdf_md_list, MD_DIR)


def test_find_indices_blank_docs(indices_mismatch_blank_docs):
    mismatch_docs_indices, empty_mismatch_docs_indices = indices_mismatch_blank_docs
    if len(mismatch_docs_indices)==0:
        print("no docs with mismatch num pages")
    if len(empty_mismatch_docs_indices)==0:
        print("no empty docs with mismatch num pages")


def test_docling_reload_and_split(load_initials, indices_mismatch_blank_docs, redocling):
    MD_DIR, MD_PYMUPDF_DIR, MD_DOCLING_DIR, docs_pdf = load_initials
    mismatch_docs_indices, empty_mismatch_docs_indices = indices_mismatch_blank_docs
    if len(empty_mismatch_docs_indices)==0:
        print("no empty docs with mismatched num pages" \
        "so no redocling happened")
    else:
        docling_pages_md_list = redocling
        u1.save_obj(MD_DOCLING_DIR, 'pages_redocling.pkl', docling_pages_md_list)


def test_punctuation_correction(load_initials, indices_mismatch_blank_docs, punctuation_gemini):
    MD_DIR, MD_PYMUPDF_DIR, MD_DOCLING_DIR, docs_pdf = load_initials
    mismatch_docs_indices, empty_mismatch_docs_indices = indices_mismatch_blank_docs
    if len(empty_mismatch_docs_indices)==0:
        print("no empty docs with mismatched num pages" \
        "so no punctuation needed")
    else:
        docling_pages_md_list = punctuation_gemini
        u1.save_obj(MD_DOCLING_DIR, 'pages_punctuation.pkl', docling_pages_md_list)


def test_alignment_correction(load_initials, alignment_correction):
    MD_DIR, MD_PYMUPDF_DIR, MD_DOCLING_DIR, docs_pdf = load_initials
    docling_pages_md_list = alignment_correction
    u1.save_obj(MD_DOCLING_DIR, 'pages_alignment.pkl', docling_pages_md_list)


def test_pymupdf_metadata(load_raw_md):
    pymupdf_md_list, docling_md_list = load_raw_md
    p.qa_metadata(pymupdf_md_list)


def test_modify_langpages(load_initials, modify_langpages):
    MD_DIR, MD_PYMUPDF_DIR, MD_DOCLING_DIR, docs_pdf = load_initials
    md_list = modify_langpages
    u1.save_obj(MD_DIR, 'mod_langpages.pkl', md_list)


def test_minimize_tokkens_on_non_word_pgs(load_initials, modify_langpages):
    MD_DIR, MD_PYMUPDF_DIR, MD_DOCLING_DIR, docs_pdf = load_initials
    md_list = modify_langpages
    md_list = p.place_empty_string_for_non_word_pgs(md_list)
    if cfg_pdf.save_md:
        u1.save_obj(MD_DIR, 'pdf_md_list.pkl', md_list)
        u1.save_obj(MD_DIR, 'docs_pdf.pkl', docs_pdf)
    






    


    


    


