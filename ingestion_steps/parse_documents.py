from parsers import pdf_parsers, excel_parsers, ppt_parsers, msword_parsers

def parse():
    docs_pdf, pdf_md_list = pdf_parsers.pipeline1()
    docs_excel, excel_md_list = excel_parsers.pipeline1()
    docs_pptx, ppt_md_list = ppt_parsers.pipeline1()
    docs_msword, msword_md_list = msword_parsers.pipeline1()
    