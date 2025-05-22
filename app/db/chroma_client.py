import chromadb
from chromadb.config import Settings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from  app.models.case import getCases
from sentence_transformers import SentenceTransformer
from datetime import date
# Chunks, Indexes, embeddings

def init_chromadb():
    client = chromadb.Client(Settings())
    try: client.delete_collection("case_chunks")
    except: pass
    # get or create vector collection: collection will hold your text chunks along with their embeddings and metadata
    coll = client.get_or_create_collection("case_chunks")
    # Load a sentence‐embedding model
    model    = SentenceTransformer("all-MiniLM-L6-v2", device='cpu')
    # Prepare a text splitter
    splitter = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=50)
    # iterate over cases, split texts into chunks
    # encode the chunk and generate their embeddings
    # Add encodings and chunks in collections
    for c in getCases():
        ord_dt = date.fromisoformat(c["metadata"]["date"]).toordinal()
        chunks = splitter.split_text(c["text"])
        embs   = model.encode(chunks, batch_size=16)
        for i,(chunk,vec) in enumerate(zip(chunks,embs)):
            md = {**c["metadata"], "_ord": ord_dt, "case_id": c["case_id"], "chunk_index": i}
            coll.add(
                ids=[f"{c['case_id']}_{i}"],
                documents=[chunk],
                embeddings=[vec],
                metadatas=[md]
            )
    return coll, model