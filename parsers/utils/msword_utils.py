import torch 
torch.set_float32_matmul_precision('high')
from langchain_core.documents import Document
from docling.document_converter import DocumentConverter, InputFormat, WordFormatOption, PdfFormatOption
from docling.datamodel.pipeline_options import ConvertPipelineOptions, PdfPipelineOptions
from tqdm import tqdm
from pathlib import Path
from copy import deepcopy
import os, subprocess, shutil
from parsers.utils import common_utils as u1
import re


def load_saving_paths(cfg)->tuple[Path, Path]:
    # load output paths if not exist
    MD_DIR = Path(cfg.MD_DIR)
    MSWORD2DOCX_DIR = Path(cfg.MSWORD2DOCX_DIR)
    MSWORD2PDF_DIR = Path(cfg.MSWORD2PDF_DIR)
    # create dir if not exist else give overwrite warning
    MD_DIR.mkdir(parents=True) if not MD_DIR.exists() else print("md_dir exists so it could be overwritten")
    MSWORD2DOCX_DIR.mkdir(parents=True) if not MSWORD2DOCX_DIR.exists() else print("MSWORD2DOCX_DIR exists so it could be overwritten")
    MSWORD2PDF_DIR.mkdir(parents=True) if not MSWORD2PDF_DIR.exists() else print("MSWORD2PDF_DIR exists so it could be overwritten")
    return MD_DIR, MSWORD2DOCX_DIR, MSWORD2PDF_DIR


def convert_msoffice_files_libreoffice(input_file_path:Path, output_dir_path:Path, output_ext:str="pdf")->None:
    """using terminal cli, libreoffice converts msoffice format to pdf"""
    libreoffice_path = '/usr/bin/libreoffice'
    if not os.path.exists(libreoffice_path):
        raise FileNotFoundError(f"LibreOffice executable not found at {libreoffice_path}")

    command = [
        libreoffice_path,
        '--headless',           # Run without a user interface
        '--convert-to', output_ext,  # Specify the conversion to PDF
        '--outdir', output_dir_path, # Specify the output directory
        input_file_path              # The file to convert
    ]

    try:
        subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(f"Successfully converted {input_file_path} to {output_ext} and saved in {output_dir_path}")
    except subprocess.CalledProcessError as e:
        print(f"Error during conversion: {e.stderr.decode()}")
    except FileNotFoundError:
        print(f"Error: The LibreOffice executable was not found at '{libreoffice_path}'. Please check the path.")

def convert_msword2docx(fdocs_msword:list[Path], MSWORD2DOCX_DIR:Path)->list[Path]:
    """turn doc format to docx else copy docx files to specified dir"""
    docs_docx = []
    for doc_msword in fdocs_msword:
        if doc_msword.suffix==".doc":
            convert_msoffice_files_libreoffice(doc_msword, MSWORD2DOCX_DIR, output_ext="docx")
            docs_docx.append(MSWORD2DOCX_DIR/doc_msword.with_suffix(".docx").name)
            continue
        if doc_msword.suffix==".docx":
            shutil.copy2(doc_msword,MSWORD2DOCX_DIR/doc_msword.name)
            docs_docx.append(MSWORD2DOCX_DIR/doc_msword.name)
            continue
        raise TypeError("fdocs_msword list contains other file format than  .doc, .docx")
    return docs_docx

def convert_msword2pdf(fdocs_msword:list[Path], MSWORD2PDF_DIR:Path)->list[Path]:
    msword2pdf_docs = []
    for doc_msword in fdocs_msword:
        convert_msoffice_files_libreoffice(doc_msword, MSWORD2PDF_DIR, output_ext="pdf")
        msword2pdf_docs.append(MSWORD2PDF_DIR/doc_msword.with_suffix(".pdf").name)
    return msword2pdf_docs

def old_load_raw_docx_docling(fdocs_msword:list[Path],docs_docx:list[Path], num_of_pgs_list:list[int]) -> list[list[Document]]:
    """ failed: docx has no page num metadata 
    so can not separate pages even with page_breakholder or
    loading specific page as empty result """
    # # docx do not store total pages in its metadata so workaround
    # num_of_pgs_list = [doc[0].metadata["total_pages"] for doc in pdf_raw_list]
    # """docling is internally used; output is langchain Document object with metadata"""
    pipeline_options = ConvertPipelineOptions()
    pipeline_options.allow_external_plugins = True
    doc_converter = DocumentConverter(format_options={
            InputFormat.DOCX: WordFormatOption(pipeline_options=pipeline_options)
        })
    raw_list = []
    for i,doc_docx in enumerate(tqdm(docs_docx)):
        doc = doc_converter.convert(doc_docx).document
        # pages = doc.export_to_markdown(page_break_placeholder="\n---------Page-----------\n", image_placeholder="")

        # create langchain Document for parsed markdown
        langchain_pages = []
        total_pgs = num_of_pgs_list[i]
        file_path = fdocs_msword[i]
        for page_no in range(total_pgs):
            pg_md = doc.export_to_markdown(page_no=page_no+1, image_placeholder="")
            pg = Document(
                page_content=pg_md,
                metadata={
                    "file_path": str(file_path),
                    "page": page_no + 1,
                    "total_pages": total_pgs,
                    "source": file_path.name# str(file_path).split('/')[-1]
                }
            )
            langchain_pages.append(pg)
        raw_list.append(langchain_pages)
    
    return raw_list

def load_raw_docx_docling(fdocs_msword:list[Path],docs_docx:list[Path]) -> list[str]:
    """docling is used to parse and output is markdown string of whole document
      as doc format do not store page info in metadata"""
    pipeline_options = ConvertPipelineOptions()
    pipeline_options.allow_external_plugins = True
    doc_converter = DocumentConverter(format_options={
            InputFormat.DOCX: WordFormatOption(pipeline_options=pipeline_options)
        })
    raw_list = []
    for doc_docx in tqdm(docs_docx):
        doc = doc_converter.convert(doc_docx).document
        pages = doc.export_to_markdown(image_placeholder="")
        raw_list.append(pages)
    return raw_list

def load_raw_pdf_docling(fdocs_msword:list[Path], msword2pdf_docs:list[Path]) -> list[list[Document]]:
    """docling is internally used; output is langchain Document object with metadata"""
    pipeline_options = PdfPipelineOptions()
    pipeline_options.allow_external_plugins = True
    doc_converter = DocumentConverter(format_options={
            InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
        })
    raw_list = []
    for i,con_doc in enumerate(tqdm(msword2pdf_docs)):
        doc = doc_converter.convert(con_doc).document
        # pages = doc.export_to_markdown(page_break_placeholder="\n---------Page-----------\n", image_placeholder="")

        # create langchain Document for parsed markdown
        langchain_pages = []
        total_pgs = len(doc.pages)
        file_path = fdocs_msword[i]
        for page_no in range(total_pgs):
            pg_md = doc.export_to_markdown(page_no=page_no+1, image_placeholder="")
            pg = Document(
                page_content=pg_md,
                metadata={
                    "file_path": str(file_path),
                    "page": page_no + 1,
                    "total_pages": total_pgs,
                    "source": file_path.name# str(file_path).split('/')[-1]
                }
            )
            langchain_pages.append(pg)
        raw_list.append(langchain_pages)
    
    return raw_list


def load_raw_pdf_docling_exp_simple(msword2pdf_docs:list[Path]) -> list[str]:
    """docling is internally used; output is single whole document markdown string"""
    pipeline_options = PdfPipelineOptions()
    pipeline_options.allow_external_plugins = True
    doc_converter = DocumentConverter(format_options={
            InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
        })
    raw_md_docling_list = []
    for con_doc in tqdm(msword2pdf_docs):
        doc = doc_converter.convert(con_doc).document
        pages = doc.export_to_markdown(page_break_placeholder="\n---------Page-----------\n",image_placeholder="")
        raw_md_docling_list.append(pages)
    return raw_md_docling_list


def save_raw_parse(fdocs_msword:list[Path], MSWORD2DOCX_DIR:Path, MSWORD2PDF_DIR:Path) -> None:
    """(in pickle format) saves langchain Document object for each page via docx and converted pdf mode" 
    via docling"""
    docs_docx = convert_msword2docx(fdocs_msword, MSWORD2DOCX_DIR)
    docx_raw_list = load_raw_docx_docling(fdocs_msword, docs_docx)
    u1.save_obj(MSWORD2DOCX_DIR, 'raw.pkl', docx_raw_list)
    
    msword2pdf_docs = convert_msword2pdf(fdocs_msword, MSWORD2PDF_DIR)
    pdf_raw_list = load_raw_pdf_docling(fdocs_msword, msword2pdf_docs)
    u1.save_obj(MSWORD2PDF_DIR, 'raw.pkl', pdf_raw_list)
   

def load_saved_raw_parse(MSWORD2DOCX_DIR:Path, MSWORD2PDF_DIR:Path) \
-> tuple[list[list[Document]],list[list[Document]]]:
    """loads pickle files stored by save_raw_parse"""
    docx_raw_list = u1.load_saved_obj(MSWORD2DOCX_DIR, 'raw.pkl')
    pdf_raw_list = u1.load_saved_obj(MSWORD2PDF_DIR, 'raw.pkl')
    return docx_raw_list, pdf_raw_list

def is_empty(s):
    """Return True if the string is empty or only whitespace."""
    has_word = bool(re.search(r'\w', s))
    return not has_word

def finalize(docx_raw_list:list[str], pdf_raw_list:list[list[Document]])->list[list[Document]]:
    msword_md_list = deepcopy(pdf_raw_list)
    num_of_pgs_list = [doc[0].metadata["total_pages"] for doc in pdf_raw_list]
    # [1, 1, 1, 1, 1, 1, 2, 5, 2, 2, 1, 2, 1, 1, 2, 23, 1, 1, 2]
    for i, total_pgs in enumerate(num_of_pgs_list):
        if is_empty(docx_raw_list[i]) or i==10:
            continue
        if total_pgs==1: 
            msword_md_list[i][0].page_content=docx_raw_list[i]
    return msword_md_list







