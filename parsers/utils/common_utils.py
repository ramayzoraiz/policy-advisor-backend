from pydantic import validate_call
from typing import Tuple,List
from pathlib import Path
from box import Box



@validate_call(validate_return=True)
def list_docs(docs_path:Path) -> list[Path]:
    """loads paths from cfg.yaml"""
    assert docs_path.exists(), f"docs_path not found: {docs_path.resolve()}"
    # documents under dir and check if not empty
    docs_list = sorted( p for p in docs_path.rglob("*") if p.is_file() )
    assert len(docs_list)>0, f"no file under dir: {docs_path.resolve()}"
    # set of file formats in docs 
    docs_formats = {d.suffix for d in docs_list}
    print("list of different file formats present in documents ")
    print(docs_formats)
    # quality check that no file is without extension
    assert not '' in docs_formats, "file without extension is present"

    return docs_list


def filter_ext(docs:List[Path],ext_list:List[str])-> List[Path] | List[List[Path]]:
    docs_ext_list = []
    for ext in ext_list:
        docs_ext = [d for d in docs if d.suffix==ext]
        # pdf documents under dir and check if not empty
        assert len(docs_ext)>0, f"no {ext} file found"
        docs_ext_list.append(docs_ext)
    if len(docs_ext_list)==1:
        docs_ext_list = docs_ext_list[0]
    return docs_ext_list


