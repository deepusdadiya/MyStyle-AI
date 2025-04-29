import faiss
import pandas as pd
from sklearn.preprocessing import normalize
from sentence_transformers import SentenceTransformer

# Load model and data
model = SentenceTransformer("all-MiniLM-L6-v2")   # for semantic embedding, converts text (like a user query) into a dense vector representation
index = faiss.read_index("Semantic_Search/faiss_product_index.index")
metadata = pd.read_csv("Semantic_Search/faiss_metadata.csv")

def search_products(query, top_k=20):
    query_vec = model.encode([query])   # Turns the query string into an embedding vector
    query_vec = normalize(query_vec, axis=1).astype("float32")     # Normalizes the query vector, cosine similarity
    # FAISS uses inner product for cosine similarity, so we need to normalize the query vector
    scores, indices = index.search(query_vec, top_k)    
    return metadata.iloc[indices[0]]   # Returns the top_k most similar products to the query

# Example
print(search_products("lightweight running shoes under 3000"))