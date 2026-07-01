import torch 
torch.set_float32_matmul_precision('high')
from langchain_core.documents import Document
from docling.document_converter import DocumentConverter, InputFormat, ImageFormatOption
from docling.datamodel.pipeline_options import EasyOcrOptions, PdfPipelineOptions
from tqdm import tqdm
from pathlib import Path
from copy import deepcopy
import os, subprocess, shutil
from parsers.utils import common_utils as u1
import re


def load_saving_paths(cfg)->Path:
    # load output paths if not exist
    MD_DIR = Path(cfg.MD_DIR)
    # create dir if not exist else give overwrite warning
    MD_DIR.mkdir(parents=True) if not MD_DIR.exists() else print("md_dir exists so it could be overwritten")
    return MD_DIR


def parse_raw_docling(fdocs_image:list[Path]) -> list[list[Document]]:
    """docling is internally used; output is langchain Document object with metadata"""
    # 1. Create a configuration object
    pipeline_options = PdfPipelineOptions()
    # 2. Set your core extraction rules:
    pipeline_options.allow_external_plugins = True
    pipeline_options.do_ocr = True               # Turn OCR on (set False to disable)
    pipeline_options.do_table_structure = True   # Detect and extract tables
    pipeline_options.ocr_options = EasyOcrOptions(
        # force_full_page_ocr=True, # no effect
        lang=["en"]   # Specify which languages to detect
    )

    # 2. Apply this configuration to image files
    converter = DocumentConverter(
        format_options={
            InputFormat.IMAGE: ImageFormatOption(
                pipeline_options=pipeline_options
            )
        }
    )
    
    raw_list = []
    for i,doc_image in enumerate(tqdm(fdocs_image)):
        doc = converter.convert(doc_image).document
        # pages = doc.export_to_markdown(page_break_placeholder="\n---------Page-----------\n", image_placeholder="")

        # create langchain Document for parsed markdown
        langchain_pages = []
        total_pgs = len(doc.pages)
        file_path = fdocs_image[i]
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

    del converter
    del doc
    torch.cuda.empty_cache()
    
    return raw_list


def parse_raw_docling_exp_simple(fdocs_image:list[Path]) -> list[str]:
    """docling is internally used; output is single whole document markdown string"""
    pipeline_options = PdfPipelineOptions()
    pipeline_options.allow_external_plugins = True
    pipeline_options.ocr_options = EasyOcrOptions(
        # force_full_page_ocr=True, # no effect
        lang=["en"]   # Specify which languages to detect
    )
    doc_converter = DocumentConverter(format_options={
            InputFormat.IMAGE: ImageFormatOption(pipeline_options=pipeline_options)
        })
    raw_md_docling_list = []
    for doc_image in tqdm(fdocs_image):
        doc = doc_converter.convert(doc_image).document
        pages = doc.export_to_markdown(page_break_placeholder="\n---------Page-----------\n",image_placeholder="")
        raw_md_docling_list.append(pages)
    return raw_md_docling_list








