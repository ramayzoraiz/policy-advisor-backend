import pytest
from pathlib import Path
from tests.configtest import DOCS_PATH, cfg_image
from parsers.utils import common_utils as u1
from parsers.utils import image_utils as p
ext_list=[".png", ".jpg", ".jpeg"]
DOCS_PATH=Path(DOCS_PATH)

@pytest.fixture(scope="module")
def load_initials():
    MD_DIR = p.load_saving_paths(cfg_image)
    docs = u1.list_docs( DOCS_PATH )
    docs_image = u1.filter_ext(docs, ext_list)
    fdocs_image = docs_image
    if isinstance(docs_image[0], list):
        fdocs_image = [doc_path for docs_sublist in docs_image for doc_path in docs_sublist]
    return MD_DIR, fdocs_image


@pytest.fixture(scope="module")
def load_saved_raw_parse(load_initials):
    MD_DIR, fdocs_image = load_initials
    image_raw_list = u1.load_saved_obj(MD_DIR, 'raw.pkl')
    return image_raw_list


def test_load_initials(load_initials):
    MD_DIR, fdocs_image = load_initials
    assert len(fdocs_image)>0, f"data has no image file in {DOCS_PATH}"
    assert isinstance(DOCS_PATH, Path)
    assert isinstance(MD_DIR, Path)

def test_save_raw_parse(load_initials):
    MD_DIR, fdocs_image = load_initials
    if cfg_image.fresh_save_raw:
        image_raw_list = p.parse_raw_docling(fdocs_image)
        u1.save_obj(MD_DIR, 'raw.pkl', image_raw_list)
    # Assert it is not empty for next test of loading
    assert (MD_DIR/"raw.pkl").is_file(), f"no raw.pkl file saved in {MD_DIR}"

def test_final(load_initials, load_saved_raw_parse):
    MD_DIR, fdocs_image = load_initials
    image_raw_list = load_saved_raw_parse
    image_md_list = image_raw_list
    if cfg_image.save_md:
        u1.save_obj(MD_DIR, 'image_md_list.pkl', image_md_list)
        u1.save_obj(MD_DIR, 'docs_image.pkl', fdocs_image)

    

        