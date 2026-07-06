from langchain_text_splitters import RecursiveCharacterTextSplitter
from splitters import utils
from langchain_core.documents import Document
from parsers.utils.common_utils import load_saved_obj, save_obj
from itertools import chain
from config import PARSE_OUT, SPLIT_OUT


def split():
    # docs=[docs_pdf,docs_excel,docs_pptx,docs_msword,docs_image]
    # md_list=[pdf_md_list,excel_md_list,ppt_md_list,msword_md_list,image_md_list]
    # a = {"docs":docs, "md_list":md_list}
    a=load_saved_obj(PARSE_OUT,'')
    docs=a["docs"]
    md_list=a["md_list"]

    # flatten the lists
    docs = list(chain.from_iterable(docs))
    md_list = list(chain.from_iterable(md_list))

    split_list = utils.split_documents_v2(md_list)

    save_obj(SPLIT_OUT,'',split_list)








