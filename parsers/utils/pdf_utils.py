import pymupdf.layout, pymupdf4llm
from langchain_pymupdf4llm import PyMuPDF4LLMLoader
from langchain_core.documents import Document
import torch
from docling.datamodel.pipeline_options import PdfPipelineOptions, RapidOcrOptions
from docling.document_converter import DocumentConverter, PdfFormatOption, InputFormat
from langchain_docling import DoclingLoader
from langchain_docling.loader import ExportType
import re
from pathlib import Path
import pickle
from tqdm import tqdm
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from copy import deepcopy
from google import genai
from google.genai import types

################################################################
def load_saving_paths(cfg)->tuple[Path, Path, Path]:
    # load output paths if not exist
    MD_DIR = Path(cfg.MD_DIR)
    MD_PYMUPDF_DIR = Path(cfg.MD_PYMUPDF_DIR)
    MD_DOCLING_DIR = Path(cfg.MD_DOCLING_DIR)
    # create dir if not exist else give overwrite warning
    MD_DIR.mkdir(parents=True) if not MD_DIR.exists() else print("md_dir exists so it could be overwritten")
    MD_PYMUPDF_DIR.mkdir(parents=True) if not MD_PYMUPDF_DIR.exists() else print("md_pymupdf_dir exists so it could be overwritten")
    MD_DOCLING_DIR.mkdir(parents=True) if not MD_DOCLING_DIR.exists() else print("md_docling_dir exists so it could be overwritten")
    return MD_DIR, MD_PYMUPDF_DIR, MD_DOCLING_DIR
################################################################

################################################################
def load_saved(md_dir: Path)->list[str]:
    with open(md_dir/'pdf_md_list.pkl', 'rb') as file:
        md_list = pickle.load(file)
    return md_list
################################################################

################################################################
def save_md(md_dir: Path, md_list:list[str])->None:
    with open(md_dir/'pdf_md_list.pkl', 'wb') as file:
        pickle.dump(md_list, file)
################################################################


def load_raw_md_from_pdf_by_pymupdf(docs_pdf:list[Path]) -> list[list[Document]]:
    """pymupdf4llm langchain outputs metadata, page_content for each page"""
    raw_md_from_pdf_by_pymupdf_list = []
    for doc in tqdm(docs_pdf):
        loader = PyMuPDF4LLMLoader( doc, use_ocr=False )
        pgs = loader.load() #pgs=list[Document(Pg),Document(Pg),...]
        # this for loop removes from each page 
        for pg in pgs:
            # remove **==>picture [33x444] intentionally omitted==>** from page
            pattern = (
            r"^[ \t]*(?:\*{2})?\s*==>\s*picture\s*\[\s*\d{1,4}\s*x\s*\d{1,4}\s*\]"
            r"\s*intentionally\s+omitted\s*<==\s*(?:\*{2})?[ \t]*\r?\n?")
            pg.page_content = re.sub(pattern, "", pg.page_content, flags=re.IGNORECASE|re.MULTILINE)
        raw_md_from_pdf_by_pymupdf_list.append(pgs)
    return raw_md_from_pdf_by_pymupdf_list #[list[Document(Pg),Document(Pg),...],...]

def load_raw_md_from_pdf_by_docling(docs_pdf:list[Path]) -> list[str]:
    """altough langchain docling is interbnally used; output is single whole document markdown string"""
    pipeline_options = PdfPipelineOptions()
    pipeline_options.allow_external_plugins = True
    converter = DocumentConverter(format_options={
            InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
        })
    raw_md_from_pdf_by_docling_list = []
    for doc in tqdm(docs_pdf):
        loader = DoclingLoader( file_path=doc, export_type=ExportType.MARKDOWN,
                    converter=converter,
                    md_export_kwargs={
                        "page_break_placeholder": "\n<-- Page {page} -->\n",
                        "image_placeholder":"", })  
        md = loader.load() #list[Document(Pg)]
        md = md[0].page_content #Document(Pg)-> text
        raw_md_from_pdf_by_docling_list.append(md) #list[str(md),str,...]
    return raw_md_from_pdf_by_docling_list
################################################################
def save_raw_md_from_pdf(docs_pdf:list[Path], out_pymupdf_md_dir:Path, out_docling_md_dir:Path)->None:
    """(in pickle format) saves langchain Document object for each page via "pymupdf4llm" 
    and saves single markdown for whole document via docling"""
    pymupdf_md_list = load_raw_md_from_pdf_by_pymupdf(docs_pdf)
    docling_md_list = load_raw_md_from_pdf_by_docling(docs_pdf)
    # Save the object to a file
    with open(out_pymupdf_md_dir/'raw.pkl', 'wb') as file:
        pickle.dump(pymupdf_md_list, file)
    with open(out_docling_md_dir/'raw.pkl', 'wb') as file:
        pickle.dump(docling_md_list, file)
################################################################

################################################################
def load_saved_raw_md_from_pdf(out_pymupdf_md_dir:Path, out_docling_md_dir:Path)->tuple[list[list[Document]],list[str]]:
    """loads pickle files stored by save_raw_md_from_pdf"""
    # Load the object from a file
    with open(out_pymupdf_md_dir/'raw.pkl', 'rb') as file:
        pymupdf_md_list = pickle.load(file)
    with open(out_docling_md_dir/'raw.pkl', 'rb') as file:
        docling_md_list = pickle.load(file)
    return pymupdf_md_list, docling_md_list
################################################################

################################################################
def view_save(docs_dir:Path, docs_pdf:list[Path], out_pymupdf_md_dir:Path, out_docling_md_dir:Path)->None:
    """save single-document markdown files in structural order for pymupdf4llm and docling. Useful for comparing any file"""
    pymupdf_md_list, docling_md_list = load_saved_raw_md_from_pdf(out_pymupdf_md_dir,out_docling_md_dir)
    out_pymupdf_files_path = [out_pymupdf_md_dir / path.relative_to(docs_dir) for path in docs_pdf]
    out_pymupdf_files_path = [path.with_suffix('.md') for path in out_pymupdf_files_path]
    out_docling_files_path = [out_docling_md_dir / path.relative_to(docs_dir) for path in docs_pdf]
    out_docling_files_path = [path.with_suffix('.md') for path in out_docling_files_path]
    for i in range(len(docs_pdf)):
        # pymupdf chunks joining and saving
        whole_pymupdf_file='\n\nPage\n\n'.join([pg.page_content for pg in pymupdf_md_list[i]])
        out_pymupdf_files_path[i].parent.mkdir(parents=True, exist_ok=True)
        out_pymupdf_files_path[i].write_bytes(whole_pymupdf_file.encode())
        
        whole_docling_file=docling_md_list[i]
        out_docling_files_path[i].parent.mkdir(parents=True, exist_ok=True)
        out_docling_files_path[i].write_bytes(whole_docling_file.encode())
################################################################


def qa_metadata(pymupdf_md_list:list[list[Document]])->None:
    """for each md file, extract metadata(of first page as it has enough info for whole file).
      make sure file_path and source exists and are equal"""
    for i in range(len(pymupdf_md_list)):
        pg = pymupdf_md_list[i][0]
        file_path = pg.metadata['file_path']
        assert file_path!='', f"file_path of {i} pymupdf with page 0 is empty"
        source = pg.metadata['source']
        assert source!='', f"source of {i} pymupdf with page 0 is empty"
        assert file_path == source, f"{file_path} not match with \n {source}"

def split_single_md_to_pages_md(docling_md_list:list[str])->list[list[str]]:
    docling_pages_md_list = []
    for single_doc_md in docling_md_list:
        # separator_pattern = r"\n<-- Page \d+ -->\n"
        separator_pattern = r"\n<-- Page {page} -->\n"
        single_doc_pages = re.split(separator_pattern, single_doc_md)
        docling_pages_md_list.append(single_doc_pages)
    return docling_pages_md_list
################################################################
def docling_md_splitting(docling_md_list:list[str],
              pymupdf_md_list:list[list[Document]]) -> list[list[str]]:
    """check metadata of pymupdf4llm and split docling single md to pages md for a doc and
      store index of files that have diff pages between docling and pymupdf4llm"""
    qa_metadata(pymupdf_md_list)
    docling_pages_md_list = split_single_md_to_pages_md(docling_md_list)
    return docling_pages_md_list
################################################################

################################################################
def num_of_pages_mismatch(docling_pages_md_list:list[list[str]],
              pymupdf_md_list:list[list[Document]], dir: Path):
    mismatch_index_list = []
    mismatch_detail_list = []
    for i, pymupdf_doc in enumerate(pymupdf_md_list):
        num_pages_pymupdf_doc = len(pymupdf_doc)
        num_pages_docling_doc = len(docling_pages_md_list[i])
        if num_pages_pymupdf_doc != num_pages_docling_doc:
            # store index for later analysis
            mismatch_index_list.append(i)
            mismatch_detail_list.append(f"num pages of docling md ({num_pages_docling_doc}) and pymupdf md ({num_pages_pymupdf_doc}) do not match for doc {i}")
    if len(mismatch_index_list)>0:
        print("\nWarning: some Docling and PyMuPDF4LLM md page numbers do not match! \n" \
        "Check log_mismatch_detail and log_mismatch_index\n")
        with open(dir/"log_mismatch_index.txt", 'w') as file:
            for idx in mismatch_index_list:
                file.write(f"{idx}\n")
        with open(dir/"log_mismatch_detail.txt", 'w') as file:
            for line in mismatch_detail_list:
                file.write(f"{line}\n")
################################################################


def identify_indices_of_blank_docs(indices:list[int],docling_pages_md_list:list[list[str]])->list[int]:
    """check from mismatch-index that if docling extracted pages of
      a doc are empty(do not contain a word) and return blank docs' indices"""
    empty_docs_indices=[]
    for index in indices: #[2, 12, 13, 59, 106]
        doc = docling_pages_md_list[index]
        # joining multiple pages to single text
        text = '\n\n'.join([pg for pg in doc])
        # if no content on page
        has_word = bool(re.search(r'\w', text))
        if not has_word:
            empty_docs_indices.append(index)
    return empty_docs_indices #[12, 13]

def reload_docling(doc_pdf:Path)->str:
    """reload docling with rapidocr and force it to operate on full page"""
    pipeline_options = PdfPipelineOptions()
    pipeline_options.allow_external_plugins = True
    # Force full page OCR for better detection of skewed text
    pipeline_options.ocr_options = RapidOcrOptions(
        force_full_page_ocr=True,  # Hybrid mode: OCR only where no text exists
        lang=["en"]                 # Specify languages
    )

    doc_converter = DocumentConverter(format_options={
                    InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
                })
    doc = doc_converter.convert(doc_pdf).document
    
    pages = doc.export_to_markdown(
        page_break_placeholder="\n<-- Page {page} -->\n",
        image_placeholder="",)
    return pages

def docling_reload_and_resplit(empty_docs_indices:list[int], docs_pdf:list[Path], docling_pages_md_list:list[list[str]]):
    """use empty_docs_indices to get those pdf path(via docs_pdf)
      and save reparsed md in docling_pages_md_list"""
    for index in empty_docs_indices:
        empty_doc = docs_pdf[index]
        md = reload_docling(empty_doc)
        has_word = bool(re.search(r'\w', md))
        assert has_word, f"even after docling reload, doc with index {index} is empty"
        # single md to pages md split
        separator_pattern = r"\n<-- Page {page} -->\n"
        single_doc_pages = re.split(separator_pattern, md)
        # place correctly ocr doc in list
        docling_pages_md_list[index]=single_doc_pages
    return docling_pages_md_list

def gemini_init():
    client = genai.Client()

    # 1. Define your configuration
    chat_config = types.GenerateContentConfig(
        temperature=1.0,
        system_instruction=(
            "You are an English grammar expert. Correct text according to these rules:\n"
            "- Correct spacing between words\n"
            "- Correct punctuation\n"
            "- Correct heading word order\n"
            "- Do not rephrase or summarize\n"
            "- Just respond with the corrected essay"
        )
    )

    # 2. Initialize the chat with the config
    chat = client.chats.create(
        # model="gemini-3-flash-preview",
        model = 'gemini-3.1-flash-lite',
        config=chat_config
    )

    return client, chat

def gemini_text_correction_prompt(doc_pages:list[str], chat)->list[str]:
    pgs = deepcopy(doc_pages)
    # 3. Use standard send_message
    for i in range(len(pgs)):
        response = chat.send_message(f"correct the following essay: \n\n {pgs[i]}")
        pgs[i]=response.text
    return pgs

def punctuation_correction(empty_docs_indices:list[int],docling_pages_md_list:list[list[str]])->list[list[str]]:
    """using gemini free api; correct grammer, syntax and punctuation"""
    client, chat=gemini_init()
    for idx in empty_docs_indices:
        docling_pages_md_list[idx]=gemini_text_correction_prompt(docling_pages_md_list[idx],chat)
    return docling_pages_md_list
################################################################
def blank_docs_correction_for_mismatched(docs_pdf:list[Path], docling_pages_md_list:list[list[str]], dir: Path)->list[list[str]]:
    """first load mismatch index, then reload completely blank docs,
    finally correct grammer using gemini"""
    # read mismatch index
    with open(dir/"log_mismatch_index.txt", 'r') as file:
        indices = [int(line.strip()) for line in file]
        
    # identify blank docs and reload again
    empty_docs_indices=identify_indices_of_blank_docs(indices,docling_pages_md_list) #indices=[2, 12, 13, 59, 106]
    docling_pages_md_list=docling_reload_and_resplit(empty_docs_indices, docs_pdf, docling_pages_md_list)
    docling_pages_md_list = punctuation_correction(empty_docs_indices, docling_pages_md_list)
    return docling_pages_md_list
################################################################


def is_empty(s):
    """Return True if the string is empty or only whitespace."""
    has_word = bool(re.search(r'\w', s))
    return not has_word

def cosine_sim(str1, str2):
    """
    Compute cosine similarity between two non‑empty strings using TF‑IDF.
    Returns a float between 0 and 1.
    """
    # Both strings are assumed non‑empty here
    vectorizer = TfidfVectorizer().fit([str1, str2])
    tfidf = vectorizer.transform([str1, str2])
    return cosine_similarity(tfidf[0:1], tfidf[1:2])[0][0]

def blank_pgs_correction(ref_list:list[str], text_list:list[str])->list[str]:
    jump=0
    result=[]
    ref_idx = 0
    text_idx = 0
    empty_block_head=False
    while ref_idx<len(ref_list):
    # for idx in range(len(ref_list)):
        if text_idx >= len(text_list):
            if len(result)>=len(text_list):
                result.append(ref_list[ref_idx])
                text_idx=text_idx+1
                ref_idx=ref_idx+1
        else:
            text = text_list[text_idx]
            ref = ref_list[ref_idx]
            if not is_empty(text) and not empty_block_head:
                result.append(text)
                text_idx=text_idx+1
                ref_idx=ref_idx+1
                empty_block_head = False
                continue
            if is_empty(text) and not empty_block_head:
                result.append("")
                text_idx=text_idx+1
                ref_idx=ref_idx+1
                empty_block_head=True
                continue
            if not is_empty(text) and empty_block_head:
                if not is_empty(ref):
                    result.append(text)
                    text_idx=text_idx+1
                    ref_idx=ref_idx+1
                    empty_block_head=False
                if is_empty(ref):
                    matched = False
                    for i in range(4):
                        jump = i + 1
                        if ref_idx+jump >= len(ref_list)-1:
                            result.append(text)
                            ref_idx=ref_idx+1
                            text_idx=text_idx+1
                            empty_block_head=False
                            break
                        sim = cosine_sim(text, ref_list[ref_idx+jump])
                        if sim > 0.75:
                            # result.append(text)
                            matched = True
                            break
                    if matched:
                        # insert blank pages in between
                        matched=False
                        for i in range(jump):
                            ref_idx=ref_idx+1
                            result.append("")
                        result.append(text)
                        ref_idx=ref_idx+1
                        text_idx=text_idx+1
                        empty_block_head=False
                        jump=0

            if is_empty(text) and empty_block_head:
                result.append("")
                ref_idx=ref_idx+1
                text_idx=text_idx+1
                empty_block_head = True
                continue
    return result
################################################################
def mismatch_pages_alignment_correction(docs_pdf:list[Path], docling_pages_md_list:list[list[str]], 
                              pymupdf_md_list:list[list[Document]], dir:Path)->list[list[str]]:
    """first load mismatch index, then correct misaligned pages due to blank/error pages   """
    # read mismatch index
    with open(dir/"log_mismatch_index.txt", 'r') as file:
        indices = [int(line.strip()) for line in file]
    # convert list[list[Document]] -> list[list[str]]
    mod_pymupdf_md_list = [[langpg.page_content for langpg in doc] for doc in pymupdf_md_list]
    # again identify docs with mismatch pages after eliminating blank and docling them
    pages_mismatch_docs_indices=[]
    for index in indices: #[2,12,13,59,106]
        if len(mod_pymupdf_md_list[index])!=len(docling_pages_md_list[index]):
            pages_mismatch_docs_indices.append(index)
    pages_mismatch_docs_indices.sort()           
    # correct mismatch pages due to multiple blank pages skipped
    for index in pages_mismatch_docs_indices:
        docling_pages_md_list[index]=blank_pgs_correction(mod_pymupdf_md_list[index],docling_pages_md_list[index])
        num_pages_pymupdf=len(mod_pymupdf_md_list[index])
        num_pages_docling=len(docling_pages_md_list[index])
        assert num_pages_pymupdf==num_pages_docling, f"mismatch pages correction failed with doc index:{index}, name{docs_pdf[index]}; conflict: pgs_pymupdf({num_pages_pymupdf}), pgs_docling({num_pages_docling})"
    
    return docling_pages_md_list
################################################################



def modify_langpages(docling_pages_md_list:list[list[str]],
              pymupdf_md_list:list[list[Document]]) -> list[list[Document]]:
    """update pymupdf text to correct text from docling list 
    and include page_no and source in metadata"""
    # till now, docling page_content ready
    md_list = deepcopy(pymupdf_md_list)
    # it contains langpage, swap with right content
    for lang_doc, text_doc in zip(md_list,docling_pages_md_list):
        for lang_pg, pg in zip(lang_doc,text_doc):
            lang_pg.page_content = pg
            lang_pg.metadata['page']=lang_pg.metadata['page']+1
            lang_pg.metadata['source']=lang_pg.metadata['source'].split('/')[-1]
            # total_pages, file_path are same
    return md_list
    


def place_empty_string_for_non_word_pgs(md_list:list[list[Document]])->list[list[Document]]:
    """standardize empty pages to '' instead of '\n\n'"""
    for i,md_pages in enumerate(md_list):
        for n,pg in enumerate(md_pages):
            if is_empty(pg.page_content):
                # print(f"doc {i} pg {n} is empty")
                pg.page_content=''
    return md_list


