import openai
import json
import os
import faiss
import pandas as pd
from sklearn.preprocessing import normalize
from sentence_transformers import SentenceTransformer

load_dotenv()
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

SYSTEM_PROMPT = """
You are a helpful assistant that extracts product filters from a user query for a fashion e-commerce site.
Return the following fields in valid JSON:
- gender: "men" or "women" or null
- price_min: integer or null
- price_max: integer or null
- category: one of "shoes", "shirts", "t-shirts", "jeans", "trousers", or null

Examples:
Input: "show me men shoes between 3000 to 4000"
Output: {"gender": "men", "category": "shoes", "price_min": 3000, "price_max": 4000}

Input: "cheap women jeans"
Output: {"gender": "women", "category": "jeans", "price_min": null, "price_max": null}
"""
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))  
def extract_filters_with_llm(query: str):
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": query}
        ],
        temperature=0
    )

    content = response.choices[0].message.content
    try:
        return json.loads(content)
    except Exception as e:
        print("❌ JSON parse failed:", e)
        return {"gender": None, "category": None, "price_min": None, "price_max": None}


# Example
print(search_products("lightweight running shoes under 3000"))