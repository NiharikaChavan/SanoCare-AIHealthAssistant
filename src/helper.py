from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader, TextLoader, Docx2txtLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain_core.documents import Document
from datetime import datetime
import os
import requests
import json
from dotenv import load_dotenv
from src.database import db, Conversation, User
from flask_login import current_user
from langchain_huggingface import HuggingFaceEmbeddings
from pinecone import Pinecone
from typing import List, Dict

#Extract Data From the PDF File
def load_pdf_file(data):
    loader = DirectoryLoader(data,
                           glob="*.pdf",
                           loader_cls=PyPDFLoader)
    documents = loader.load()
    return documents

#Split the Data into Text Chunks
def text_split(extracted_data):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=20)
    text_chunks = text_splitter.split_documents(extracted_data)
    return text_chunks

#Download the Embeddings from HuggingFace 
def download_hugging_face_embeddings():
    """Download and return HuggingFace embeddings"""
    return HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

def log_conversation(session_id, user_ip, user_message, bot_response):
    """Log conversation to database for authenticated users"""
    print("\n=== log_conversation called ===")
    print("Current user:", current_user)
    print("Is authenticated:", current_user.is_authenticated if current_user else False)
    
    # Strict authentication check at the start
    if not current_user or not current_user.is_authenticated:
        print("Error: Attempted to log conversation for non-authenticated user")
        return
        
    try:
        print("\nAttempting to log conversation:")
        print(f"User authenticated: {current_user.is_authenticated}")
        print(f"User ID: {current_user.user_id}")
        print(f"Session ID: {session_id}")
        print(f"Message length: {len(user_message)}")
        print(f"Response length: {len(bot_response)}")
        
        # Additional validation for authenticated user
        if not current_user.user_id:
            print("Error: User ID not found for authenticated user")
            return
            
        # Verify user exists in database
        user = User.query.get(current_user.user_id)
        if not user:
            print("Error: User not found in database")
            return
            
        if not session_id:
            print("Error: No session_id provided")
            return
            
        new_entry = Conversation(
            session_id=session_id,
            user_ip=user_ip,
            message=user_message,
            bot_response=bot_response,
            user_id=current_user.user_id
        )
        db.session.add(new_entry)
        db.session.commit()
        print("Successfully logged conversation")
    except Exception as e:
        db.session.rollback()
        print(f"Database logging failed: {str(e)}")
        print("Stack trace:", e.__traceback__)

def load_snomed_data() -> List[Dict]:
    """Load SNOMED CT clinical terminology focusing on symptoms and their relationships"""
    try:
        # SNOMED CT API endpoint (requires authentication)
        snomed_url = "https://browser.ihtsdotools.org/snowstorm/snomed-ct/browser/MAIN/2023-01-31/concepts"
        headers = {
            'Authorization': f"Bearer {os.getenv('SNOMED_API_KEY')}",
            'Accept': 'application/json'
        }
        
        # Define key symptom categories and their root concept IDs
        symptom_categories = {
            'finding': '404684003',  # Finding
            'symptom': '418799008',  # Symptom
            'sign': '365730000',     # Sign
            'pain': '22253000',      # Pain
            'fever': '386661006',    # Fever
            'headache': '25064002',  # Headache
            'nausea': '422587007',   # Nausea
            'fatigue': '84229001',   # Fatigue
            'cough': '49727002',     # Cough
            'shortness_of_breath': '267036007',  # Shortness of breath
            'chest_pain': '29857009',  # Chest pain
            'abdominal_pain': '21522001',  # Abdominal pain
            'dizziness': '247441003',  # Dizziness
            'vomiting': '422400008',   # Vomiting
            'diarrhea': '62315008'     # Diarrhea
        }
        
        processed_data = []
        
        # Get concepts for each symptom category
        for category, root_id in symptom_categories.items():
            params = {
                'ecl': f'< {root_id}',  # Get all descendants
                'limit': 100,  # Limit per category
                'active': True,  # Only active concepts
                'form': 'inferred'  # Include inferred relationships
            }
            
            response = requests.get(snomed_url, headers=headers, params=params, timeout=30)
            
            if response.status_code == 401:
                print("Unauthorized: Invalid SNOMED API key")
                continue
            elif response.status_code != 200:
                print(f"SNOMED API returned status code: {response.status_code}")
                print(f"Response content: {response.text}")
                continue
                
            snomed_data = response.json()
            
            for concept in snomed_data.get('items', []):
                if concept.get('active', False):
                    # Get detailed relationships
                    relationships = concept.get('relationships', [])
                    
                    # Filter relationships by type
                    related_symptoms = []
                    severity = None
                    location = None
                    duration = None
                    
                    for rel in relationships:
                        rel_type = rel.get('typeId')
                        target = rel.get('targetId')
                        
                        # Map relationship types
                        if rel_type == '116680003':  # Is a
                            related_symptoms.append(target)
                        elif rel_type == '246112005':  # Severity
                            severity = target
                        elif rel_type == '272741003':  # Laterality
                            location = target
                        elif rel_type == '246454002':  # Occurrence
                            duration = target
                    
                    processed_data.append({
                        'title': concept.get('term', ''),
                        'description': concept.get('description', ''),
                        'code': concept.get('conceptId', ''),
                        'type': 'symptom',
                        'category': category,
                        'relationships': {
                            'related_symptoms': related_symptoms[:3],
                            'severity': severity,
                            'location': location,
                            'duration': duration
                        },
                        'parent_concepts': concept.get('parentIds', [])
                    })
            
            print(f"Loaded {len(processed_data)} concepts for category: {category}")
        
        print(f"Total loaded symptom concepts: {len(processed_data)}")
        return processed_data
            
    except requests.exceptions.Timeout:
        print("Timeout while fetching SNOMED data")
        return []
    except requests.exceptions.RequestException as e:
        print(f"Error loading SNOMED data: {str(e)}")
        return []
    except Exception as e:
        print(f"Unexpected error loading SNOMED data: {str(e)}")
        return []

def load_icd10_data() -> List[Dict]:
    """Load ICD-10 disease classification data"""
    try:
        # WHO ICD-10 API endpoint
        icd10_url = "https://icd.who.int/browse10/2019/en/JsonApi/GetCategories?useHtml=false"
        headers = {
            'Accept': 'application/json'
        }
        response = requests.get(icd10_url, headers=headers, timeout=30)
        if response.status_code == 200:
            icd10_data = response.json()
            return [{
                'title': item.get('title', ''),
                'description': item.get('description', ''),
                'code': item.get('code', ''),
                'type': 'disease'
            } for item in icd10_data]
        else:
            print(f"ICD-10 API returned status code: {response.status_code}")
            print(f"Response content: {response.text}")
    except requests.exceptions.Timeout:
        print("Timeout while fetching ICD-10 data")
    except requests.exceptions.RequestException as e:
        print(f"Error loading ICD-10 data: {str(e)}")
    return []

def load_drugbank_data() -> List[Dict]:
    """Load DrugBank medication information"""
    try:
        # DrugBank API endpoint (requires authentication)
        drugbank_url = "https://api.drugbank.com/v1/drug_names"
        headers = {
            'Authorization': f"Bearer {os.getenv('DRUGBANK_API_KEY')}",
            'Accept': 'application/json'
        }
        response = requests.get(drugbank_url, headers=headers, timeout=30)
        if response.status_code == 200:
            drug_data = response.json()
            return [{
                'title': drug.get('name', ''),
                'description': drug.get('description', ''),
                'type': 'medication',
                'interactions': drug.get('interactions', []),
                'side_effects': drug.get('side_effects', [])
            } for drug in drug_data]
        elif response.status_code == 401:
            print("Unauthorized: Invalid DrugBank API key")
        else:
            print(f"DrugBank API returned status code: {response.status_code}")
            print(f"Response content: {response.text}")
    except requests.exceptions.Timeout:
        print("Timeout while fetching DrugBank data")
    except requests.exceptions.RequestException as e:
        print(f"Error loading DrugBank data: {str(e)}")
    return []

def load_clinical_guidelines() -> List[Dict]:
    """Load clinical guidelines from various sources"""
    guidelines = []
    
    try:
        # WHO Guidelines API
        who_url = "https://apps.who.int/iris/rest/search?query=subject:guidelines&format=json&pageSize=100"
        headers = {
            'Accept': 'application/json'
        }
        who_response = requests.get(who_url, headers=headers, timeout=30)
        if who_response.status_code == 200:
            who_data = who_response.json()
            guidelines.extend([{
                'title': doc.get('title', ''),
                'description': doc.get('abstract', ''),
                'source': 'WHO',
                'type': 'guideline',
                'url': doc.get('url', '')
            } for doc in who_data.get('response', {}).get('docs', [])])
        else:
            print(f"WHO API returned status code: {who_response.status_code}")
            print(f"Response content: {who_response.text}")
        
        # CDC Guidelines (using RSS feed)
        cdc_url = "https://www.cdc.gov/guidelines/rss/guidelines.xml"
        cdc_response = requests.get(cdc_url, timeout=30)
        if cdc_response.status_code == 200:
            # Parse XML response
            from xml.etree import ElementTree
            root = ElementTree.fromstring(cdc_response.content)
            for item in root.findall('.//item'):
                guidelines.append({
                    'title': item.find('title').text if item.find('title') is not None else '',
                    'description': item.find('description').text if item.find('description') is not None else '',
                    'source': 'CDC',
                    'type': 'guideline',
                    'url': item.find('link').text if item.find('link') is not None else ''
                })
        else:
            print(f"CDC RSS feed returned status code: {cdc_response.status_code}")
            
    except requests.exceptions.Timeout:
        print("Timeout while fetching clinical guidelines")
    except requests.exceptions.RequestException as e:
        print(f"Error loading clinical guidelines: {str(e)}")
    except Exception as e:
        print(f"Unexpected error loading clinical guidelines: {str(e)}")
    
    return guidelines

def process_medical_data(data: List[Dict], source: str) -> List[Dict]:
    """Process and format medical data for embedding with optimized text length"""
    processed_data = []
    for item in data:
        # Create a concise but informative text representation based on source
        if source == 'SNOMED':
            # Build a detailed symptom description
            text_parts = [f"Symptom: {item.get('title', '')}"]
            
            # Add category
            if item.get('category'):
                text_parts.append(f"Category: {item.get('category')}")
            
            # Add description if available
            if item.get('description'):
                text_parts.append(f"Description: {item.get('description')}")
            
            # Add relationships
            relationships = item.get('relationships', {})
            if relationships:
                if relationships.get('severity'):
                    text_parts.append(f"Severity: {relationships['severity']}")
                if relationships.get('location'):
                    text_parts.append(f"Location: {relationships['location']}")
                if relationships.get('duration'):
                    text_parts.append(f"Duration: {relationships['duration']}")
                if relationships.get('related_symptoms'):
                    text_parts.append(f"Related symptoms: {', '.join(relationships['related_symptoms'])}")
            
            text = " | ".join(text_parts)
            
        elif source == 'ICD10':
            text = f"Disease: {item.get('title', '')} - {item.get('description', '')}"
        elif source == 'DrugBank':
            text = f"Medication: {item.get('title', '')} - {item.get('description', '')}"
            if item.get('side_effects'):
                text += f" Side effects: {', '.join(item['side_effects'][:3])}"
        else:  # Clinical Guidelines
            text = f"Guideline: {item.get('title', '')} - {item.get('description', '')}"
        
        processed_item = {
            'text': text,
            'metadata': {
                'source': source,
                'type': item.get('type', 'general'),
                'date': datetime.now().isoformat(),
                'code': item.get('code', ''),  # Include code for reference
                'category': item.get('category', '')  # Include category for symptoms
            }
        }
        processed_data.append(processed_item)
    return processed_data

def get_pinecone_stats():
    """Get current Pinecone index statistics"""
    try:
        index = pinecone.Index("sanocare")
        stats = index.describe_index_stats()
        return {
            'total_vectors': stats.total_vector_count,
            'namespaces': stats.namespaces
        }
    except Exception as e:
        print(f"Error getting Pinecone stats: {str(e)}")
        return None

def optimize_data_for_pinecone(data: List[Dict], max_vectors: int = 1_900_000) -> List[Dict]:
    """Optimize data to stay within Pinecone limits and minimize costs"""
    try:
        # Get current stats
        stats = get_pinecone_stats()
        if not stats:
            print("Warning: Could not get Pinecone stats. Proceeding with default limits.")
            current_vectors = 0
        else:
            current_vectors = stats['total_vectors']
        
        # Calculate how many vectors we can add
        available_space = max_vectors - current_vectors
        
        if available_space <= 0:
            print("Warning: Pinecone index is full. Consider upgrading or cleaning up old data.")
            return []
        
        # Score and filter data based on relevance and recency
        scored_data = []
        current_time = datetime.now()
        
        for item in data:
            score = 0
            
            # Handle Document objects
            if hasattr(item, 'page_content'):
                text = item.page_content
                metadata = item.metadata
            else:
                text = item.get('text', '')
                metadata = item.get('metadata', {})
            
            # Score based on source reliability
            source_scores = {
                'WHO': 10,
                'SNOMED': 9,
                'ICD10': 8,
                'DrugBank': 7,
                'Clinical Guidelines': 6,
                'CDC': 5,
                'PubMed': 4
            }
            score += source_scores.get(metadata.get('source', ''), 0)
            
            # Score based on recency (if date available)
            if 'date' in metadata:
                try:
                    item_date = datetime.fromisoformat(metadata['date'])
                    days_old = (current_time - item_date).days
                    if days_old < 30:  # Recent content gets higher score
                        score += 5
                    elif days_old < 90:  # Moderately recent content
                        score += 3
                except:
                    pass
            
            # Score based on content quality
            if len(text) > 100:  # Longer content might be more detailed
                score += 2
            if any(keyword in text.lower() for keyword in ['treatment', 'diagnosis', 'symptoms', 'prevention']):
                score += 3
            
            scored_data.append((score, item))
        
        # Sort by score and take top items
        scored_data.sort(reverse=True)
        return [item for _, item in scored_data[:available_space]]
        
    except Exception as e:
        print(f"Error optimizing data for Pinecone: {str(e)}")
        return []

def load_medical_documents(directory_path):
    """Load medical documents from various formats"""
    try:
        if not os.path.exists(directory_path):
            print(f"Directory not found: {directory_path}")
            return []
        
        documents = []
        
        # Load PDF files
        pdf_loader = DirectoryLoader(
            directory_path,
            glob="**/*.pdf",
            loader_cls=PyPDFLoader
        )
        try:
            pdf_docs = pdf_loader.load()
            documents.extend(pdf_docs)
        except Exception as e:
            print(f"Error loading PDF files: {str(e)}")
        
        # Load text files
        text_loader = DirectoryLoader(
            directory_path,
            glob="**/*.txt",
            loader_cls=TextLoader
        )
        try:
            text_docs = text_loader.load()
            documents.extend(text_docs)
        except Exception as e:
            print(f"Error loading text files: {str(e)}")
        
        # Load Word documents
        docx_loader = DirectoryLoader(
            directory_path,
            glob="**/*.docx",
            loader_cls=Docx2txtLoader
        )
        try:
            docx_docs = docx_loader.load()
            documents.extend(docx_docs)
        except Exception as e:
            print(f"Error loading Word documents: {str(e)}")
        
        # Split documents into chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len
        )
        
        split_docs = text_splitter.split_documents(documents)
        return split_docs
        
    except Exception as e:
        print(f"Error loading medical documents: {str(e)}")
        return []

def fetch_realtime_medical_data():
    """Fetch real-time medical data from various sources"""
    try:
        data = []
        
        # WHO data
        who_data = get_who_data('India')
        if who_data:
            data.append(Document(
                page_content=str(who_data),
                metadata={"source": "WHO", "type": "health_data"}
            ))
        
        # Add more data sources as needed
        
        return data
    except Exception as e:
        print(f"Error fetching real-time medical data: {str(e)}")
        return []

def fetch_cdc_alerts():
    """Fetch CDC health alerts and updates"""
    try:
        cdc_url = "https://emergency.cdc.gov/han/feed.asp"
        response = requests.get(cdc_url, timeout=30)
        if response.status_code == 200:
            # Parse RSS feed
            from xml.etree import ElementTree
            root = ElementTree.fromstring(response.content)
            alerts = []
            for item in root.findall('.//item'):
                alerts.append({
                    'title': item.find('title').text if item.find('title') is not None else '',
                    'description': item.find('description').text if item.find('description') is not None else '',
                    'date': item.find('pubDate').text if item.find('pubDate') is not None else '',
                    'type': 'CDC Alert'
                })
            return alerts
    except Exception as e:
        print(f"Error fetching CDC alerts: {str(e)}")
    return []

def fetch_pubmed_articles():
    """Fetch recent medical articles from PubMed"""
    try:
        pubmed_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
        params = {
            'db': 'pubmed',
            'term': 'medical[Title/Abstract] AND ("last 7 days"[PDat])',
            'retmode': 'json',
            'retmax': 100
        }
        response = requests.get(pubmed_url, params=params, timeout=30)
        if response.status_code == 200:
            data = response.json()
            articles = []
            for id in data.get('esearchresult', {}).get('idlist', []):
                # Get article details
                article_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
                article_params = {
                    'db': 'pubmed',
                    'id': id,
                    'retmode': 'json'
                }
                article_response = requests.get(article_url, params=article_params, timeout=30)
                if article_response.status_code == 200:
                    article_data = article_response.json()
                    article = article_data.get('result', {}).get(id, {})
                    articles.append({
                        'title': article.get('title', ''),
                        'abstract': article.get('abstract', ''),
                        'date': article.get('pubdate', ''),
                        'type': 'PubMed Article'
                    })
            return articles
    except Exception as e:
        print(f"Error fetching PubMed articles: {str(e)}")
    return []

def update_knowledge_base():
    """Update the knowledge base with all medical data, optimized for cost and with duplicate checking"""
    try:
        # Initialize Pinecone client
        pc = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))
        
        # Get current stats
        index = pc.Index("sanocare")
        stats = index.describe_index_stats()
        if not stats:
            print("Failed to get Pinecone stats. Aborting update.")
            return None
            
        current_vectors = stats.total_vector_count
        print(f"Current vector count: {current_vectors}")
        
        # Load documents
        print("Loading medical documents...")
        documents = load_medical_documents("Data")
        
        # Fetch real-time data
        print("Fetching real-time medical data...")
        realtime_data = fetch_realtime_medical_data()
        
        # Create structured knowledge documents
        print("Creating structured knowledge documents...")
        structured_docs = create_medical_knowledge_documents()
        
        # Process real-time data with better organization
        processed_realtime_docs = []
        for doc in realtime_data:
            # Add more detailed metadata for better retrieval
            doc.metadata.update({
                "data_type": "realtime",
                "timestamp": datetime.now().isoformat(),
                "priority": "high",  # Real-time data gets higher priority
                "source": doc.metadata.get("source", "WHO"),
                "category": "current_health_data"
            })
            processed_realtime_docs.append(doc)
        
        # Combine all documents with priority ordering
        all_documents = processed_realtime_docs + documents + structured_docs
        
        # Create embeddings
        embeddings = download_hugging_face_embeddings()
        
        # Create vector store
        vectorstore = PineconeVectorStore.from_existing_index(
            index_name="sanocare",
            embedding=embeddings
        )
        
        # Track progress
        total_docs = len(all_documents)
        processed_docs = 0
        skipped_docs = 0
        failed_docs = 0
        
        # Process documents in batches with duplicate checking
        batch_size = 100
        for i in range(0, total_docs, batch_size):
            batch = all_documents[i:i + batch_size]
            batch_texts = []
            batch_metadatas = []
            
            for doc in batch:
                try:
                    # Check if document already exists
                    existing_docs = vectorstore.similarity_search(
                        doc.page_content,
                        k=1,
                        filter={
                            "source": doc.metadata.get("source", ""),
                            "type": doc.metadata.get("type", ""),
                            "data_type": doc.metadata.get("data_type", ""),
                            "timestamp": doc.metadata.get("timestamp", "")
                        }
                    )
                    
                    if existing_docs:
                        # Check if content is similar enough to be considered a duplicate
                        if existing_docs[0].page_content == doc.page_content:
                            print(f"Skipping duplicate document: {doc.metadata.get('source', 'Unknown')}")
                            skipped_docs += 1
                            continue
                    
                    batch_texts.append(doc.page_content)
                    batch_metadatas.append(doc.metadata)
                    processed_docs += 1
                    
                except Exception as e:
                    print(f"Error processing document: {str(e)}")
                    failed_docs += 1
                    continue
            
            if batch_texts:
                try:
                    vectorstore.add_texts(batch_texts, metadatas=batch_metadatas)
                    print(f"Added batch {i//batch_size + 1} of {(total_docs + batch_size - 1)//batch_size}")
                    print(f"Progress: {processed_docs}/{total_docs} documents processed")
                except Exception as e:
                    print(f"Error adding batch to Pinecone: {str(e)}")
                    failed_docs += len(batch_texts)
        
        # Get updated stats
        new_stats = index.describe_index_stats()
        if new_stats:
            print("\n=== Update Summary ===")
            print(f"Total documents processed: {total_docs}")
            print(f"Successfully added: {processed_docs}")
            print(f"Skipped duplicates: {skipped_docs}")
            print(f"Failed to process: {failed_docs}")
            print(f"Updated vector count: {new_stats.total_vector_count}")
            print(f"Added {new_stats.total_vector_count - current_vectors} new vectors")
            print(f"Real-time documents added: {len(processed_realtime_docs)}")
        
        return vectorstore
        
    except Exception as e:
        print(f"Error updating knowledge base: {str(e)}")
        return None

def is_high_relevance(item):
    """Check if an item is highly relevant for storage"""
    # Define relevance criteria
    high_relevance_keywords = [
        'treatment', 'diagnosis', 'symptoms', 'prevention',
        'guidelines', 'recommendations', 'emergency', 'critical'
    ]
    
    text = item.get('text', '').lower()
    source = item.get('metadata', {}).get('source', '').lower()
    
    # Check if item meets high relevance criteria
    has_keywords = any(keyword in text for keyword in high_relevance_keywords)
    is_recent = 'date' in item.get('metadata', {})
    is_reliable_source = source in ['who', 'snomed', 'icd10', 'drugbank']
    
    return has_keywords and (is_recent or is_reliable_source)

def cleanup_old_data(max_age_days: int = 30):
    """Clean up old data from Pinecone to free up space"""
    try:
        index = pinecone.Index("sanocare")
        stats = index.describe_index_stats()
        
        # Get all vectors with metadata
        query_response = index.query(
            vector=[0] * 384,  # dummy vector
            top_k=10000,
            include_metadata=True
        )
        
        # Filter vectors older than max_age_days
        current_time = datetime.now()
        old_vectors = []
        
        for match in query_response.matches:
            metadata = match.metadata
            if 'date' in metadata:
                vector_date = datetime.fromisoformat(metadata['date'])
                if (current_time - vector_date).days > max_age_days:
                    old_vectors.append(match.id)
        
        if old_vectors:
            # Delete old vectors
            index.delete(ids=old_vectors)
            print(f"Deleted {len(old_vectors)} old vectors")
            
        return len(old_vectors)
        
    except Exception as e:
        print(f"Error cleaning up old data: {str(e)}")
        return 0

def create_medical_knowledge_documents():
    """Create structured medical knowledge documents for different regions and demographics"""
    documents = []
    
    # Region-specific medical information
    regions = {
        "India": {
            "traditional_medicine": [
                "Ayurveda principles and practices",
                "Traditional Chinese Medicine (TCM) in India",
                "Homeopathy in Indian context",
                "Yoga and meditation practices",
                "Siddha medicine",
                "Unani medicine"
            ],
            "common_conditions": [
                "Tropical diseases",
                "Dengue fever",
                "Malaria",
                "Tuberculosis",
                "Diabetes in Indian population",
                "Cardiovascular diseases",
                "Respiratory infections"
            ],
            "cultural_practices": [
                "Dietary restrictions and preferences",
                "Family-centric healthcare decisions",
                "Religious considerations in treatment",
                "Traditional healing methods",
                "Fasting practices",
                "Herbal remedies"
            ]
        },
        "China": {
            "traditional_medicine": [
                "Traditional Chinese Medicine (TCM)",
                "Acupuncture",
                "Herbal medicine",
                "Qigong",
                "Tai Chi",
                "Cupping therapy"
            ],
            "common_conditions": [
                "Respiratory conditions",
                "Digestive disorders",
                "Traditional medicine syndromes",
                "Chronic conditions",
                "Mental health patterns"
            ],
            "cultural_practices": [
                "Yin-Yang balance",
                "Five elements theory",
                "Seasonal health practices",
                "Family-based care",
                "Traditional dietary therapy"
            ]
        },
        "Japan": {
            "traditional_medicine": [
                "Kampo medicine",
                "Shiatsu massage",
                "Reiki healing",
                "Traditional herbal medicine",
                "Zen medicine practices"
            ],
            "common_conditions": [
                "Stress-related conditions",
                "Longevity practices",
                "Preventive medicine",
                "Mental health approaches",
                "Lifestyle diseases"
            ],
            "cultural_practices": [
                "Mind-body connection",
                "Preventive healthcare",
                "Work-life balance",
                "Traditional dietary practices",
                "Community health practices"
            ]
        },
        "Europe": {
            "traditional_medicine": [
                "Western herbal medicine",
                "Homeopathy",
                "Naturopathy",
                "Traditional European medicine",
                "Aromatherapy"
            ],
            "common_conditions": [
                "Chronic diseases",
                "Mental health conditions",
                "Lifestyle-related diseases",
                "Age-related conditions",
                "Environmental health issues"
            ],
            "cultural_practices": [
                "Evidence-based medicine",
                "Preventive healthcare",
                "Social healthcare systems",
                "Holistic approaches",
                "Traditional healing methods"
            ]
        },
        "Hispanic": {
            "traditional_medicine": [
                "Curanderismo practices",
                "Traditional herbal remedies",
                "Folk medicine traditions",
                "Spiritual healing practices",
                "Traditional massage"
            ],
            "common_conditions": [
                "Diabetes in Hispanic population",
                "Hypertension patterns",
                "Genetic conditions",
                "Cultural health beliefs",
                "Mental health patterns"
            ],
            "cultural_practices": [
                "Family involvement in healthcare",
                "Traditional dietary practices",
                "Religious healing traditions",
                "Language considerations",
                "Community health practices"
            ]
        },
        "American": {
            "traditional_medicine": [
                "Western medicine practices",
                "Alternative medicine approaches",
                "Evidence-based treatments",
                "Modern healthcare systems",
                "Integrative medicine"
            ],
            "common_conditions": [
                "Chronic conditions",
                "Mental health patterns",
                "Lifestyle-related diseases",
                "Insurance considerations",
                "Preventive health"
            ],
            "cultural_practices": [
                "Individual healthcare decisions",
                "Modern dietary trends",
                "Healthcare system navigation",
                "Preventive care practices",
                "Technology-based health"
            ]
        }
    }
    
    # Age-specific medical information
    age_groups = {
        "child": {
            "developmental_stages": [
                "Infant development",
                "Toddler health",
                "School-age health",
                "Growth and development",
                "Early childhood nutrition",
                "Physical activity needs"
            ],
            "common_conditions": [
                "Childhood illnesses",
                "Vaccination schedules",
                "Nutritional needs",
                "Physical development",
                "Behavioral health",
                "Learning disabilities"
            ],
            "care_approaches": [
                "Child-friendly communication",
                "Parent involvement",
                "Play-based interventions",
                "Safety considerations",
                "Educational support",
                "Family-centered care"
            ]
        },
        "adolescent": {
            "developmental_stages": [
                "Puberty changes",
                "Emotional development",
                "Social development",
                "Identity formation",
                "Cognitive development",
                "Physical growth"
            ],
            "common_conditions": [
                "Acne",
                "Mental health concerns",
                "Nutritional needs",
                "Physical development",
                "Substance use",
                "Reproductive health"
            ],
            "care_approaches": [
                "Privacy considerations",
                "Peer influence",
                "Risk-taking behaviors",
                "Future planning",
                "Educational support",
                "Mental health support"
            ]
        },
        "adult": {
            "health_concerns": [
                "Work-life balance",
                "Stress management",
                "Preventive care",
                "Chronic conditions",
                "Reproductive health",
                "Career health"
            ],
            "common_conditions": [
                "Cardiovascular health",
                "Mental health",
                "Reproductive health",
                "Lifestyle diseases",
                "Occupational health",
                "Family health"
            ],
            "care_approaches": [
                "Evidence-based treatments",
                "Lifestyle modifications",
                "Preventive measures",
                "Health maintenance",
                "Workplace wellness",
                "Family health management"
            ]
        },
        "elderly": {
            "health_concerns": [
                "Age-related conditions",
                "Mobility issues",
                "Cognitive health",
                "Social isolation",
                "Nutritional needs",
                "Medication management"
            ],
            "common_conditions": [
                "Arthritis",
                "Heart disease",
                "Diabetes",
                "Memory concerns",
                "Vision problems",
                "Hearing loss"
            ],
            "care_approaches": [
                "Gentle communication",
                "Fall prevention",
                "Medication management",
                "Quality of life",
                "Social support",
                "End-of-life care"
            ]
        }
    }
    
    # Create documents for each region
    for region, categories in regions.items():
        for category, topics in categories.items():
            for topic in topics:
                doc = Document(
                    page_content=f"Medical information for {region} region regarding {category}: {topic}",
                    metadata={
                        "region": region,
                        "category": category,
                        "type": "regional",
                        "topic": topic,
                        "source": "medical_knowledge_base",
                        "timestamp": datetime.now().isoformat()
                    }
                )
                documents.append(doc)
    
    # Create documents for each age group
    for age_group, categories in age_groups.items():
        for category, topics in categories.items():
            for topic in topics:
                doc = Document(
                    page_content=f"Medical information for {age_group} age group regarding {category}: {topic}",
                    metadata={
                        "age_group": age_group,
                        "category": category,
                        "type": "age_specific",
                        "topic": topic,
                        "source": "medical_knowledge_base",
                        "timestamp": datetime.now().isoformat()
                    }
                )
                documents.append(doc)
    
    return documents

def get_relevant_medical_info(msg, docsearch, user_context=None):
    """Get relevant medical information with cultural and demographic context, optimized for cost"""
    try:
        # Extract key terms from the message
        key_terms = extract_key_terms(msg)
        
        # First, try to get real-time data that matches the query
        realtime_info = docsearch.similarity_search(
            msg,
            k=1,
            filter={
                "data_type": "realtime",
                "priority": "high"
            }
        )
        
        # Get base medical information with limited results
        medical_info = docsearch.similarity_search(
            msg,
            k=2,
            filter={
                "type": {"$in": ["symptom", "disease", "treatment", "guideline"]}
            }
        )
        
        # Combine real-time and medical info
        combined_info = realtime_info + medical_info
        
        if user_context:
            # Get region-specific information
            region = user_context.get("region", "general")
            region_info = docsearch.similarity_search(
                f"{region} region medical information",
                k=1,
                filter={
                    "type": "regional",
                    "region": region
                }
            )
            combined_info.extend(region_info)
            
            # Get age-specific information
            age_group = user_context.get("age_group", "adult")
            age_info = docsearch.similarity_search(
                f"{age_group} age group medical information",
                k=1,
                filter={
                    "type": "age_specific",
                    "age_group": age_group
                }
            )
            combined_info.extend(age_info)
            
            # Add cultural-specific information if available
            if user_context.get("cultural_preferences"):
                cultural_info = docsearch.similarity_search(
                    f"cultural preferences {user_context['cultural_preferences']} medical information",
                    k=1,
                    filter={
                        "type": "cultural"
                    }
                )
                combined_info.extend(cultural_info)
        
        # Remove duplicates and prioritize real-time data
        unique_info = []
        seen_texts = set()
        
        # First add real-time data
        for info in combined_info:
            if info.metadata.get("data_type") == "realtime":
                text = info.page_content
                if text not in seen_texts:
                    seen_texts.add(text)
                    unique_info.append(info)
        
        # Then add other information
        for info in combined_info:
            if info.metadata.get("data_type") != "realtime":
                text = info.page_content
                if text not in seen_texts:
                    seen_texts.add(text)
                    unique_info.append(info)
        
        # Sort by relevance and recency
        unique_info.sort(key=lambda x: (
            x.metadata.get("priority", "low") == "high",  # Real-time data first
            x.metadata.get("timestamp", ""),  # Most recent next
            len(x.page_content)  # Longer content last
        ), reverse=True)
        
        return unique_info[:3]  # Return top 3 most relevant results
        
    except Exception as e:
        print(f"Error getting relevant medical information: {str(e)}")
        return []

def extract_key_terms(text):
    """Extract key medical terms from text"""
    # Common medical terms and their categories
    medical_terms = {
        'symptoms': ['pain', 'fever', 'cough', 'headache', 'nausea', 'fatigue'],
        'conditions': ['diabetes', 'hypertension', 'asthma', 'arthritis'],
        'treatments': ['medication', 'therapy', 'surgery', 'exercise'],
        'body_parts': ['head', 'chest', 'stomach', 'back', 'legs', 'arms']
    }
    
    text = text.lower()
    key_terms = []
    
    for category, terms in medical_terms.items():
        for term in terms:
            if term in text:
                key_terms.append(term)
    
    return key_terms

def update_pinecone_index(docsearch, documents):
    """Update Pinecone index with new medical knowledge documents"""
    try:
        # Add documents to the index
        docsearch.add_documents(documents)
        print(f"Successfully added {len(documents)} documents to Pinecone index")
        return True
    except Exception as e:
        print(f"Error updating Pinecone index: {str(e)}")
        return False

def get_who_data(country):
    """Get WHO data for a specific country"""
    try:
        # WHO API endpoint
        url = "https://ghoapi.azureedge.net/api/Indicator"
        
        # Make request
        response = requests.get(url)
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"WHO API returned status code: {response.status_code}")
            print(f"Response content: {response.text}")
            return None
    except Exception as e:
        print(f"Error getting WHO data: {str(e)}")
        return None

def process_gale_encyclopedia_content(content, region, age_group):
    """Process Gale Encyclopedia content with cultural and demographic context"""
    try:
        # Define region-specific medical practices
        region_specific_practices = {
            'India': {
                'traditional_medicine': ['Ayurveda', 'Yoga', 'Unani'],
                'dietary_practices': ['Vegetarian', 'Ayurvedic diet'],
                'cultural_considerations': ['Family-centric decisions', 'Respect for elders']
            },
            'Hispanic': {
                'traditional_medicine': ['Curanderismo', 'Herbal remedies'],
                'dietary_practices': ['Traditional Mexican diet', 'Mediterranean diet'],
                'cultural_considerations': ['Family involvement', 'Spiritual healing']
            },
            'American': {
                'traditional_medicine': ['Western medicine', 'Complementary medicine'],
                'dietary_practices': ['Standard American diet', 'Organic foods'],
                'cultural_considerations': ['Individual autonomy', 'Evidence-based approach']
            }
        }
        
        # Define age-specific communication styles
        age_specific_communication = {
            'child': {
                'language_level': 'simple',
                'tone': 'friendly',
                'examples': 'playful',
                'duration': 'short'
            },
            'adolescent': {
                'language_level': 'clear',
                'tone': 'supportive',
                'examples': 'relatable',
                'duration': 'moderate'
            },
            'adult': {
                'language_level': 'professional',
                'tone': 'direct',
                'examples': 'practical',
                'duration': 'detailed'
            },
            'elderly': {
                'language_level': 'clear',
                'tone': 'respectful',
                'examples': 'familiar',
                'duration': 'patient'
            }
        }
        
        # Get region-specific practices
        region_practices = region_specific_practices.get(region, region_specific_practices['American'])
        
        # Get age-specific communication style
        communication_style = age_specific_communication.get(age_group, age_specific_communication['adult'])
        
        # Process content with cultural context
        processed_content = {
            'original_content': content,
            'region_specific': {
                'traditional_medicine': region_practices['traditional_medicine'],
                'dietary_practices': region_practices['dietary_practices'],
                'cultural_considerations': region_practices['cultural_considerations']
            },
            'age_specific': {
                'communication_style': communication_style,
                'language_level': communication_style['language_level'],
                'tone': communication_style['tone']
            }
        }
        
        return processed_content
        
    except Exception as e:
        print(f"Error processing Gale Encyclopedia content: {str(e)}")
        return None

def create_cultural_medical_knowledge():
    """Create culturally and demographically specific medical knowledge documents"""
    documents = []
    
    # Define regions and age groups
    regions = ['India', 'Hispanic', 'American']
    age_groups = ['child', 'adolescent', 'adult', 'elderly']
    
    # Load Gale Encyclopedia content
    try:
        gale_content = load_gale_encyclopedia()
        
        for region in regions:
            for age_group in age_groups:
                # Process each medical condition with cultural context
                for condition in gale_content:
                    processed_content = process_gale_encyclopedia_content(
                        condition,
                        region,
                        age_group
                    )
                    
                    if processed_content:
                        # Create document with metadata
                        doc = Document(
                            page_content=str(processed_content),
                            metadata={
                                'source': 'Gale Encyclopedia',
                                'region': region,
                                'age_group': age_group,
                                'condition': condition.get('name', ''),
                                'type': 'cultural_medical',
                                'timestamp': datetime.now().isoformat()
                            }
                        )
                        documents.append(doc)
        
        print(f"Created {len(documents)} cultural medical knowledge documents")
        return documents
        
    except Exception as e:
        print(f"Error creating cultural medical knowledge: {str(e)}")
        return []

def get_cultural_treatment_suggestions(condition, user_context):
    """Get culturally and demographically appropriate treatment suggestions"""
    try:
        # Extract user context
        region = user_context.get('region', 'American')
        age_group = user_context.get('age_group', 'adult')
        cultural_preferences = user_context.get('cultural_preferences', {})
        
        # Create search query with cultural context
        search_query = f"{condition} treatment {region} {age_group}"
        
        # Get relevant medical information
        medical_info = docsearch.similarity_search(
            search_query,
            k=3,
            filter={
                "type": "cultural_medical",
                "region": region,
                "age_group": age_group
            }
        )
        
        # Process and format treatment suggestions
        suggestions = []
        for info in medical_info:
            content = json.loads(info.page_content)
            
            # Add traditional medicine if culturally appropriate
            if cultural_preferences.get('traditional_medicine'):
                suggestions.extend(content['region_specific']['traditional_medicine'])
            
            # Add dietary recommendations
            suggestions.extend(content['region_specific']['dietary_practices'])
            
            # Add cultural considerations
            suggestions.extend(content['region_specific']['cultural_considerations'])
        
        return suggestions
        
    except Exception as e:
        print(f"Error getting cultural treatment suggestions: {str(e)}")
        return []

def update_medical_history(user_id, condition, treatment, cultural_context):
    """Update user's medical history with cultural context"""
    try:
        user = User.query.get(user_id)
        if not user:
            return False
        
        # Get existing medical history
        medical_history = user.medical_history or []
        
        # Create new medical record with cultural context
        new_record = {
            'condition': condition,
            'treatment': treatment,
            'date': datetime.now().isoformat(),
            'cultural_context': cultural_context,
            'region': user.region,
            'age_group': user.age_group
        }
        
        # Add to medical history
        medical_history.append(new_record)
        
        # Update user's medical history
        user.medical_history = medical_history
        db.session.commit()
        
        return True
        
    except Exception as e:
        print(f"Error updating medical history: {str(e)}")
        db.session.rollback()
        return False

def fetch_region_specific_health_data(region):
    """Fetch region-specific health data from various sources"""
    try:
        region_data = {}
        
        # WHO Regional Data
        who_url = f"https://apps.who.int/gho/data/node.main.{region}"
        who_response = requests.get(who_url, timeout=30)
        if who_response.status_code == 200:
            region_data['who'] = who_response.json()
        
        # CDC Regional Data
        cdc_url = f"https://www.cdc.gov/healthdata/{region.lower()}/index.html"
        cdc_response = requests.get(cdc_url, timeout=30)
        if cdc_response.status_code == 200:
            region_data['cdc'] = cdc_response.text
        
        # PubMed Regional Research
        pubmed_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
        pubmed_params = {
            'db': 'pubmed',
            'term': f'({region} AND health AND culture)',
            'retmode': 'json',
            'retmax': 100
        }
        pubmed_response = requests.get(pubmed_url, params=pubmed_params, timeout=30)
        if pubmed_response.status_code == 200:
            region_data['pubmed'] = pubmed_response.json()
        
        return region_data
        
    except Exception as e:
        print(f"Error fetching region-specific health data: {str(e)}")
        return None

def fetch_cultural_health_practices(region, ethnicity):
    """Fetch cultural health practices and traditional medicine information"""
    try:
        cultural_data = {}
        
        # WHO Traditional Medicine Database
        who_tm_url = "https://apps.who.int/iris/rest/search"
        who_tm_params = {
            'query': f'traditional medicine {region} {ethnicity}',
            'format': 'json'
        }
        who_tm_response = requests.get(who_tm_url, params=who_tm_params, timeout=30)
        if who_tm_response.status_code == 200:
            cultural_data['traditional_medicine'] = who_tm_response.json()
        
        # PubMed Cultural Medicine Research
        pubmed_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
        pubmed_params = {
            'db': 'pubmed',
            'term': f'cultural medicine {region} {ethnicity}',
            'retmode': 'json',
            'retmax': 100
        }
        pubmed_response = requests.get(pubmed_url, params=pubmed_params, timeout=30)
        if pubmed_response.status_code == 200:
            cultural_data['research'] = pubmed_response.json()
        
        return cultural_data
        
    except Exception as e:
        print(f"Error fetching cultural health practices: {str(e)}")
        return None

def create_region_specific_documents(region_data, cultural_data):
    """Create documents with region-specific and cultural medical information"""
    documents = []
    
    try:
        # Process WHO data
        if 'who' in region_data:
            for item in region_data['who'].get('fact', []):
                doc = Document(
                    page_content=f"WHO Health Data for {item.get('region', '')}: {item.get('value', '')}",
                    metadata={
                        'source': 'WHO',
                        'region': item.get('region', ''),
                        'type': 'health_statistics',
                        'date': datetime.now().isoformat()
                    }
                )
                documents.append(doc)
        
        # Process CDC data
        if 'cdc' in region_data:
            doc = Document(
                page_content=f"CDC Health Information for region: {region_data['cdc']}",
                metadata={
                    'source': 'CDC',
                    'type': 'health_guidelines',
                    'date': datetime.now().isoformat()
                }
            )
            documents.append(doc)
        
        # Process PubMed data
        if 'pubmed' in region_data:
            for article in region_data['pubmed'].get('esearchresult', {}).get('idlist', []):
                doc = Document(
                    page_content=f"Research Article ID: {article}",
                    metadata={
                        'source': 'PubMed',
                        'type': 'research',
                        'date': datetime.now().isoformat()
                    }
                )
                documents.append(doc)
        
        # Process cultural data
        if cultural_data:
            if 'traditional_medicine' in cultural_data:
                for item in cultural_data['traditional_medicine'].get('response', {}).get('docs', []):
                    doc = Document(
                        page_content=f"Traditional Medicine: {item.get('title', '')}",
                        metadata={
                            'source': 'WHO Traditional Medicine',
                            'type': 'cultural_practice',
                            'date': datetime.now().isoformat()
                        }
                    )
                    documents.append(doc)
            
            if 'research' in cultural_data:
                for article in cultural_data['research'].get('esearchresult', {}).get('idlist', []):
                    doc = Document(
                        page_content=f"Cultural Medicine Research: {article}",
                        metadata={
                            'source': 'PubMed',
                            'type': 'cultural_research',
                            'date': datetime.now().isoformat()
                        }
                    )
                    documents.append(doc)
        
        return documents
        
    except Exception as e:
        print(f"Error creating region-specific documents: {str(e)}")
        return []

def update_region_specific_knowledge():
    """Update the knowledge base with region-specific and cultural medical information"""
    try:
        # Define regions and ethnicities
        regions = ['India', 'China', 'Japan', 'Europe', 'Hispanic', 'American']
        ethnicities = {
            'India': ['Indian', 'South Asian'],
            'China': ['Chinese', 'East Asian'],
            'Japan': ['Japanese', 'East Asian'],
            'Europe': ['European', 'Western'],
            'Hispanic': ['Mexican', 'Puerto Rican', 'Cuban'],
            'American': ['African American', 'Asian American', 'Native American']
        }
        
        all_documents = []
        
        for region in regions:
            # Fetch region-specific data
            region_data = fetch_region_specific_health_data(region)
            
            # Fetch cultural data for each ethnicity in the region
            for ethnicity in ethnicities.get(region, []):
                cultural_data = fetch_cultural_health_practices(region, ethnicity)
                
                # Create documents
                documents = create_region_specific_documents(region_data, cultural_data)
                all_documents.extend(documents)
        
        # Update Pinecone index
        if all_documents:
            vectorstore = PineconeVectorStore.from_existing_index(
                index_name="sanocare",
                embedding=download_hugging_face_embeddings()
            )
            vectorstore.add_documents(all_documents)
            print(f"Successfully added {len(all_documents)} region-specific documents")
        
        return all_documents
        
    except Exception as e:
        print(f"Error updating region-specific knowledge: {str(e)}")
        return []
