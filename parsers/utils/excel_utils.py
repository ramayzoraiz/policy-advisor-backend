import torch 
torch.set_float32_matmul_precision('high')
from langchain_core.documents import Document
from docling.datamodel.pipeline_options import ConvertPipelineOptions
from docling.document_converter import DocumentConverter, InputFormat, ExcelFormatOption
from tqdm import tqdm
from pathlib import Path
from google import genai
from copy import deepcopy

def load_saving_paths(cfg)->Path:
    # load output paths if not exist
    MD_DIR = Path(cfg.MD_DIR)
    # create dir if not exist else give overwrite warning
    MD_DIR.mkdir(parents=True) if not MD_DIR.exists() else print("md_dir exists so it could be overwritten")
    return MD_DIR

def load_raw_docling(docs_excel:list[Path]) -> list[list[Document]]:
    """docling is internally used; output is langchain Document object with metadata"""
    pipeline_options = ConvertPipelineOptions(allow_external_plugins = True)
    doc_converter = DocumentConverter(format_options={
            InputFormat.XLSX: ExcelFormatOption(pipeline_options=pipeline_options)
        })
    raw_md_docling_list = []
    for doc_excel in tqdm(docs_excel):
        doc = doc_converter.convert(doc_excel).document
        # pages = doc.export_to_markdown(page_break_placeholder="\n---------Page-----------\n")
    
        # create langchain Document for parsed markdown
        langchain_pages = []
        for page_no in range(len(doc.pages)):
            pg_md = doc.export_to_markdown(page_no=page_no+1,image_placeholder="")
            pg = Document(
                page_content=pg_md,
                metadata={
                    "file_path": str(doc_excel),
                    "page": page_no + 1,
                    "total_pages": len(doc.pages),
                    "source": str(doc_excel).split('/')[-1]
                }
            )
            langchain_pages.append(pg)
        raw_md_docling_list.append(langchain_pages)
    
    return raw_md_docling_list
    
def load_raw_docling_exp_simple(docs_excel:list[Path]) -> list[str]:
    """docling is internally used; output is single whole document markdown string"""
    pipeline_options = ConvertPipelineOptions(allow_external_plugins = True)
    doc_converter = DocumentConverter(format_options={
            InputFormat.XLSX: ExcelFormatOption(pipeline_options=pipeline_options)
        })
    raw_md_docling_list = []
    for doc_excel in tqdm(docs_excel):
        doc = doc_converter.convert(doc_excel).document
        pages = doc.export_to_markdown(page_break_placeholder="\n---------Page-----------\n")
        raw_md_docling_list.append(pages)
    return raw_md_docling_list
    
def gemini_table_correction_prompt(doc_page:str)->str:   
    client = genai.Client()
    # 1. Define your configuration
    chat_config = genai.types.GenerateContentConfig(
        temperature=1.0,
        system_instruction=(
            "You are an tables expert in markdown. Correct table according to these rules:\n"
            "- initial few rows of table may be actually description of table that is mistakenly added in table columns. Remove it from table cells and put info above table. make it heading for table.\n"
            "- Correct syntax if needed\n"
            "- Correct heading word order\n"
            "- Do not rephrase or summarize or add words on your own\n"
            "- Just respond with the corrected tables\n"
            "- If needed you can split or merge tables. each column of table should represent field info"
        )
    )
    # 2. Initialize the chat with the config
    chat = client.chats.create(
        # model="gemini-3-flash-preview",
        model = 'gemini-3.1-flash-lite',
        config=chat_config
    )
    # 3. Use standard send_message
    response = chat.send_message(f"correct the following tables: \n\n {doc_page}")
    pg=response.text
    return pg

def table_correction(raw_md_docling_list:list[list[Document]])->list[list[Document]]:
    excel_md_list=deepcopy(raw_md_docling_list)
    for doc in excel_md_list:
        for lang_pg in doc:
            pg = lang_pg.page_content
            lang_pg.page_content = gemini_table_correction_prompt(pg)
    return excel_md_list





