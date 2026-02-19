import os
import shutil
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from dotenv import load_dotenv

load_dotenv()

# --- CONFIGURATION ---
CHROMA_PATH = "chroma_db"
DATA_PATH = "books"

def main():
    # 1. Clear existing database to avoid duplicates from split files
    if os.path.exists(CHROMA_PATH):
        print(f"Clearing existing database at {CHROMA_PATH}...")
        shutil.rmtree(CHROMA_PATH)

    # 2. Load all PDFs from the /books folder
    print("Loading PDFs...")
    all_docs = []
    for file in os.listdir(DATA_PATH):
        if file.endswith(".pdf"):
            file_path = os.path.join(DATA_PATH, file)
            loader = PyPDFLoader(file_path)
            all_docs.extend(loader.load())

    # 3. Split into overlapping chunks
    # chunk_size: total length of each segment
    # chunk_overlap: the amount of text shared between neighbors
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=150,
        length_function=len,
        add_start_index=True,
    )
    
    chunks = text_splitter.split_documents(all_docs)
    print(f"Split {len(all_docs)} pages into {len(chunks)} overlapping chunks.")

    # 4. Create and persist the Vector Database
    print("Generating embeddings and saving to ChromaDB...")
    vector_db = Chroma.from_documents(
        chunks, 
        OpenAIEmbeddings(), 
        persist_directory=CHROMA_PATH
    )
    
    print(f"✅ Success! Database created at {CHROMA_PATH}")

if __name__ == "__main__":
    main()