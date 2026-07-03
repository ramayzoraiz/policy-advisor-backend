from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from config import cfg_split as cs

def split_documents(documents: list[list[Document]]):
    """
    Split documents into smaller chunks for better retrieval.
    
    Args:
        documents: DocObj=pg, list[DocObj]=pgs of a doc, list[list[DocObj]]=pgs of docs
        
    Returns:
        List of split Document chunks
    """
    if not documents:
        print("empty documents argument in split_documents function")
        return []
    
    print(f"\n✂️  Splitting documents into chunks...")
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=cs.CHUNK_SIZE,
        chunk_overlap=cs.CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", ", ", " ", ""],
        # length_function=len
    )
    
    split_docs = []

    for doc in documents:
        doc_chunks = text_splitter.split_documents(doc)
        # Add paragraph-level metadata
        for i, chunk in enumerate(doc_chunks):
            chunk.metadata["chunk_id"] = i
            chunk.metadata["char_count"] = len(chunk.page_content)
        split_docs.append(doc_chunks)
        
        print(f"   ✓ Created {len(doc_chunks)} chunks of {doc[0].metadata["source"]}")
        print(f"   📊 Average chunk size: {sum(len(c.page_content) for c in doc_chunks) // len(doc_chunks)} characters")
    
    return split_docs



