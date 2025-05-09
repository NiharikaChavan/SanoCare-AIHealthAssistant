import os
import sys
from dotenv import load_dotenv
from helper import (
    load_medical_documents,
    fetch_realtime_medical_data,
    create_medical_knowledge_documents,
    update_knowledge_base,
    update_region_specific_knowledge
)
from pinecone import Pinecone

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

def main():
    """Initialize the medical knowledge base"""
    try:
        print("Starting knowledge base initialization...")
        
        # Load environment variables
        load_dotenv()
        
        # Initialize Pinecone client
        pc = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))
        
        # Get existing index
        index = pc.Index("sanocare")
        print("Connected to existing Pinecone index: sanocare")
        
        # Update knowledge base
        print("\nUpdating medical knowledge base...")
        vectorstore = update_knowledge_base()
        
        if vectorstore:
            print("\nUpdating region-specific knowledge...")
            region_docs = update_region_specific_knowledge()
            
            if region_docs:
                print(f"Successfully added {len(region_docs)} region-specific documents")
            else:
                print("No region-specific documents were added")
        else:
            print("Failed to update knowledge base")
            
    except Exception as e:
        print(f"Error initializing knowledge base: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 