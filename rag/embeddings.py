import os
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
from dotenv import load_dotenv

load_dotenv()

model_name = os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5").strip()
EF_INSTANCE = SentenceTransformerEmbeddingFunction(model_name=model_name)

def get_embedding_function():
    return EF_INSTANCE

document_embedding_function = get_embedding_function
query_embedding_function = get_embedding_function


