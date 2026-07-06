from parsers import pdf_parsers, excel_parsers, \
ppt_parsers, msword_parsers, image_parsers
from parsers.utils.common_utils import save_obj
from pathlib import Path
from config import PARSE_OUT

def parse():
    docs_pdf, pdf_md_list = pdf_parsers.pipeline1()
    docs_excel, excel_md_list = excel_parsers.pipeline1()
    docs_pptx, ppt_md_list = ppt_parsers.pipeline1()
    docs_msword, msword_md_list = msword_parsers.pipeline1()
    docs_image, image_md_list = image_parsers.pipeline1()
    docs=[docs_pdf,docs_excel,docs_pptx,docs_msword,docs_image]
    md_list=[pdf_md_list,excel_md_list,ppt_md_list,msword_md_list,image_md_list]
    save_obj(PARSE_OUT,'',{"docs":docs, "md_list":md_list})

    