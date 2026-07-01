from pathlib import Path
from parsers.utils import common_utils as u1
from parsers.utils import image_utils as p
from copy import deepcopy
from config import DOCS_PATH, cfg_image
ext_list=[".png", ".jpg", ".jpeg"] #2,2,13
DOCS_PATH = Path(DOCS_PATH)

def pipeline1():
    MD_DIR = p.load_saving_paths(cfg_image)
    docs = u1.list_docs( DOCS_PATH )
    docs_image = u1.filter_ext(docs, ext_list)
    # flatten out nested list of .doc and .docx into one
    fdocs_image = docs_image
    if isinstance(docs_image[0], list):
        fdocs_image = [doc_path for docs_sublist in docs_image for doc_path in docs_sublist]
    
    if cfg_image.return_saved:
        return fdocs_image, u1.load_saved_obj(MD_DIR, 'image_md_list.pkl')
    if cfg_image.fresh_save_raw:
        image_raw_list = p.parse_raw_docling(fdocs_image)
        u1.save_obj(MD_DIR, 'raw.pkl', image_raw_list)
    image_raw_list = u1.load_saved_obj(MD_DIR, 'raw.pkl')
        
    image_md_list = image_raw_list
    if cfg_image.save_md:
        u1.save_obj(MD_DIR, 'image_md_list.pkl', image_md_list)
    return fdocs_image, image_md_list

def pipeline2():
    pass
