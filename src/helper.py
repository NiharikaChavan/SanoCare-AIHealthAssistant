from langchain.document_loaders import PyPDFLoader, DirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import HuggingFaceEmbeddings
import requests

from requests.adapters import HTTPAdapter
from urllib3 import Retry
from src.database import db, Conversation
from flask_login import current_user


#Extract Data From the PDF File
def load_pdf_file(data):
    loader= DirectoryLoader(data,
                            glob="*.pdf",
                            loader_cls=PyPDFLoader)

    documents=loader.load()

    return documents



#Split the Data into Text Chunks
def text_split(extracted_data):
    text_splitter=RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=20)
    text_chunks=text_splitter.split_documents(extracted_data)
    return text_chunks



#Download the Embeddings from HuggingFace 
def download_hugging_face_embeddings():
    embeddings=HuggingFaceEmbeddings(model_name='sentence-transformers/all-MiniLM-L6-v2')  #this model return 384 dimensions
    return embeddings

# def get_who_data(region, indicator="MORTALITY"):
#     user_region = 'India'
#     url = f"https://ghoapi.azureedge.net/api/{indicator}?$filter=Region eq '{user_region}'"
#     who_data = requests.get(url).json()
#     return who_data

# def get_who_data(region, indicator="MORTALITY"):
#     user_region = region  # region passed as argument
#     url = f"https://ghoapi.azureedge.net/api/{indicator}?$filter=Region eq '{user_region}'"
    
#     response = requests.get(url)
#     print("Response Status Code:", response.status_code)
#     print("Response Content:", response.text)  # Print the raw response
    
#     if response.status_code == 200:
#         if response.text.strip():  # If response is not empty
#             try:
#                 who_data = response.json()
#             except requests.exceptions.JSONDecodeError:
#                 who_data = {"error": "Invalid JSON response."}
#         else:
#             who_data = {"error": "Empty response received."}
#     else:
#         who_data = {"error": f"Request failed with status code: {response.status_code}"}
    
#     return who_data

COUNTRY_ISO_MAP = {
    "India": "IND",
    "Nigeria": "NGA",
    "United States": "USA",
    # Add all countries you support
}


def get_who_data(country_name="India", indicator="MDG_0000000026", year=None):
    # Step 1: Validate country code
    iso_code = COUNTRY_ISO_MAP.get(country_name)
    if not iso_code:
        return {"error": f"Invalid country: {country_name}. Use ISO3 codes."}

    # Step 2: Build URL with valid parameters
    base_url = f"https://ghoapi.azureedge.net/api/{indicator}"
    filters = [f"COUNTRY eq '{iso_code}'"]
    if year:
        filters.append(f"YEAR eq {year}")
    url = f"{base_url}?$filter={' and '.join(filters)}"

    # Step 3: Configure retries for 500 errors
    session = requests.Session()
    retries = Retry(
        total=3,
        backoff_factor=0.3,
        status_forcelist=[500, 502, 503, 504]
    )
    session.mount("https://", HTTPAdapter(max_retries=retries))

    try:
        response = session.get(url, timeout=10)
        response.raise_for_status()  # Throw HTTP errors
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": f"API failed: {str(e)}"}

    
def log_conversation(session_id, user_ip, user_message, bot_response, region, who_data):
    # Skip storage completely if user is not authenticated
    if not current_user.is_authenticated:
        print("Skipping conversation storage - user not authenticated")
        return
        
    try:
        new_entry = Conversation(
            session_id=session_id,
            user_ip=user_ip,
            message=user_message,
            bot_response=bot_response,
            user_id=current_user.user_id
        )
        db.session.add(new_entry)
        db.session.commit()
        print("Conversation stored for authenticated user")
    except Exception as e:
        db.session.rollback()
        print(f"Database logging failed: {str(e)}")
