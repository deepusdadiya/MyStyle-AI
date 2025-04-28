import faiss
import pandas as pd
from sklearn.preprocessing import normalize
from sentence_transformers import SentenceTransformer

# Load model and data
model = SentenceTransformer("all-MiniLM-L6-v2")
index = faiss.read_index("Semantic Search/faiss_product_index.index")
metadata = pd.read_csv("Semantic Search/faiss_metadata.csv")

def search_products(query, top_k=20):
    query_vec = model.encode([query])
    query_vec = normalize(query_vec, axis=1).astype("float32")
    scores, indices = index.search(query_vec, top_k)
    
    return metadata.iloc[indices[0]]

# Example
print(search_products("lightweight running shoes under 3000"))