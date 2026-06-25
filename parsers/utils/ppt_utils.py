import torch 
torch.set_float32_matmul_precision('high')
from langchain_core.documents import Document
from docling.document_converter import DocumentConverter, InputFormat, PowerpointFormatOption
from docling.pipeline.vlm_pipeline import VlmPipeline
from tqdm import tqdm
from pathlib import Path
from copy import deepcopy
import os, subprocess


def load_saving_paths(cfg)->tuple[Path, Path]:
    # load output paths if not exist
    MD_DIR = Path(cfg.MD_DIR)
    PPT2PDF_DIR = Path(cfg.PPT2PDF_DIR)
    # create dir if not exist else give overwrite warning
    MD_DIR.mkdir(parents=True) if not MD_DIR.exists() else print("md_dir exists so it could be overwritten")
    PPT2PDF_DIR.mkdir(parents=True) if not PPT2PDF_DIR.exists() else print("ppt2pdf_dir exists so it could be overwritten")
    return MD_DIR, PPT2PDF_DIR


def convert_msoffice_to_pdf_libreoffice(input_file_path:Path, output_dir_path:Path)->None:
    """using terminal cli, libreoffice converts msoffice format to pdf"""
    libreoffice_path = '/usr/bin/libreoffice'
    if not os.path.exists(libreoffice_path):
        raise FileNotFoundError(f"LibreOffice executable not found at {libreoffice_path}")

    command = [
        libreoffice_path,
        '--headless',           # Run without a user interface
        '--convert-to', 'pdf',  # Specify the conversion to PDF
        '--outdir', output_dir_path, # Specify the output directory
        input_file_path              # The file to convert
    ]

    try:
        subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(f"Successfully converted {input_file_path} to PDF and saved in {output_dir_path}")
    except subprocess.CalledProcessError as e:
        print(f"Error during conversion: {e.stderr.decode()}")
    except FileNotFoundError:
        print(f"Error: The LibreOffice executable was not found at '{libreoffice_path}'. Please check the path.")


def convert_ppt2pdf(docs_ppt:list[Path], PPT2PDF_DIR:Path)->list[Path]:
    ppt2pdf_docs = []
    for doc_ppt in docs_ppt:
        convert_msoffice_to_pdf_libreoffice(doc_ppt, output_dir_path=PPT2PDF_DIR)
        ppt2pdf_docs.append(PPT2PDF_DIR/doc_ppt.with_suffix(".pdf").name)
    return ppt2pdf_docs


def load_raw_docling(docs_ppt:list[Path], ppt2pdf_docs:list[Path]) -> list[list[Document]]:
    """docling is internally used; output is langchain Document object with metadata"""
    doc_converter = DocumentConverter(format_options={
            InputFormat.PPTX: PowerpointFormatOption(
                # pipeline_options=pipeline_options,
                pipeline_cls=VlmPipeline
            )
        }
    )
    raw_md_docling_list = []
    for i,con_doc in enumerate(tqdm(ppt2pdf_docs)):
        doc = doc_converter.convert(con_doc).document
        # pages = doc.export_to_markdown(page_break_placeholder="\n---------Page-----------\n", image_placeholder="")

        # create langchain Document for parsed markdown
        langchain_pages = []
        total_pgs = len(doc.pages)
        file_path = docs_ppt[i]
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
        raw_md_docling_list.append(langchain_pages)
    
    return raw_md_docling_list


def load_raw_docling_exp_simple(ppt2pdf_docs:list[Path]) -> list[str]:
    """docling is internally used; output is single whole document markdown string"""
    doc_converter = DocumentConverter(format_options={
            InputFormat.PPTX: PowerpointFormatOption(
                # pipeline_options=pipeline_options,
                pipeline_cls=VlmPipeline
            )
        }
    )
    raw_md_docling_list = []
    for con_doc in tqdm(ppt2pdf_docs):
        doc = doc_converter.convert(con_doc).document
        pages = doc.export_to_markdown(page_break_placeholder="\n---------Page-----------\n",image_placeholder="")
        raw_md_docling_list.append(pages)
    return raw_md_docling_list
    




