import os
import shutil
from langchain_community.document_loaders import (
    PyPDFLoader, 
    TextLoader
)
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from dotenv import load_dotenv

load_dotenv()

# --- CONFIGURATION ---
CHROMA_PATH = "chroma_db"
KNOWLEDGE_FOLDERS = {
    "maritime": "books",              # Maritime safety PDFs
    "fishing_reports": "fishing_reports",  # Fishing reports (txt, md, pdf)
    "mooring_locations": "mooring_locations"  # Anchorages and moorings in the Sounds
}

def load_documents_from_folder(folder_path, category):
    """Load documents from a folder and tag them with a category."""
    docs = []
    
    if not os.path.exists(folder_path):
        print(f"⚠️ Folder not found: {folder_path}")
        return docs
    
    for file in os.listdir(folder_path):
        file_path = os.path.join(folder_path, file)
        
        try:
            if file.endswith(".pdf"):
                loader = PyPDFLoader(file_path)
                loaded_docs = loader.load()
            elif file.endswith((".txt", ".md")):
                loader = TextLoader(file_path, encoding='utf-8')
                loaded_docs = loader.load()
            else:
                continue  # Skip unsupported file types
            
            # Add category metadata to each document
            for doc in loaded_docs:
                doc.metadata['category'] = category
                doc.metadata['filename'] = file
            
            docs.extend(loaded_docs)
            print(f"  ✓ Loaded {file} ({len(loaded_docs)} pages/sections)")
            
        except Exception as e:
            print(f"  ✗ Error loading {file}: {e}")
    
    return docs

def main():
    # 1. Clear existing database to start fresh
    if os.path.exists(CHROMA_PATH):
        print(f"Clearing existing database at {CHROMA_PATH}...")
        shutil.rmtree(CHROMA_PATH)

    # 2. Load documents from all knowledge folders
    print("\n📚 Loading documents from all knowledge sources...")
    all_docs = []
    
    for category, folder_path in KNOWLEDGE_FOLDERS.items():
        print(f"\n{category.upper()}:")
        category_docs = load_documents_from_folder(folder_path, category)
        all_docs.extend(category_docs)
        print(f"  → {len(category_docs)} document(s) loaded")

    if not all_docs:
        print("\n⚠️ No documents found! Please add files to the knowledge folders.")
        return

    # 3. Split into overlapping chunks
    print(f"\n✂️ Splitting documents into chunks...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=150,
        length_function=len,
        add_start_index=True,
    )
    
    chunks = text_splitter.split_documents(all_docs)
    print(f"   Split {len(all_docs)} document(s) into {len(chunks)} chunks")

    # 4. Create and persist the Vector Database
    print(f"\n💾 Generating embeddings and saving to ChromaDB...")
    vector_db = Chroma.from_documents(
        chunks, 
        OpenAIEmbeddings(), 
        persist_directory=CHROMA_PATH
    )
    
    print(f"\n✅ SUCCESS! Knowledge base created at {CHROMA_PATH}")
    print(f"   📖 Maritime docs: {sum(1 for d in all_docs if d.metadata.get('category') == 'maritime')}")
    print(f"   🎣 Fishing reports: {sum(1 for d in all_docs if d.metadata.get('category') == 'fishing_reports')}")
    print(f"   ⚓ Mooring locations: {sum(1 for d in all_docs if d.metadata.get('category') == 'mooring_locations')}")

if __name__ == "__main__":
    main()
