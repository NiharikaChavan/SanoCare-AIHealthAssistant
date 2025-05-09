import os
from dotenv import load_dotenv
from langchain_pinecone import PineconeVectorStore
from langchain_openai import OpenAIEmbeddings
from helper import create_medical_knowledge_documents, update_pinecone_index

def init_pinecone_index():
    """Initialize Pinecone index with medical knowledge"""
    try:
        # Load environment variables
        load_dotenv()
        
        # Initialize embeddings
        embeddings = OpenAIEmbeddings()
        
        # Initialize Pinecone
        index_name = "sanocare"
        docsearch = PineconeVectorStore.from_existing_index(
            index_name=index_name,
            embedding=embeddings
        )
        
        # Create medical knowledge documents
        print("Creating medical knowledge documents...")
        documents = create_medical_knowledge_documents()
        
        # Update Pinecone index
        print(f"Updating Pinecone index with {len(documents)} documents...")
        success = update_pinecone_index(docsearch, documents)
        
        if success:
            print("Successfully initialized Pinecone index with medical knowledge")
        else:
            print("Failed to initialize Pinecone index")
            
    except Exception as e:
        print(f"Error initializing Pinecone index: {str(e)}")

if __name__ == "__main__":
    init_pinecone_index() 