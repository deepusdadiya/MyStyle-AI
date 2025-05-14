import pandas as pd 
import json
import os
from sklearn.preprocessing import normalize
import numpy as np
import ast
from alchemist.postgresql.resource import DBConnection
import httpx
import re
import pandas as pd

KRUTRIM_API_KEY = os.getenv("KRUTRIM_API_KEY")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SEMANTIC_DIR = os.path.join(BASE_DIR, "..", "Semantic_Search")

INDEX_PATH = os.path.join(SEMANTIC_DIR, "faiss_product_index.index")
METADATA_PATH = os.path.join(SEMANTIC_DIR, "faiss_metadata.csv")
EMBEDDED_PRODUCTS_CSV = os.path.join(SEMANTIC_DIR, "embedded_products.csv")
metadata = pd.read_csv(METADATA_PATH)

CATEGORY_TABLE_MAP = {
    "shoes": ["products.men_shoes", "products.women_shoes"],
    "shirts": ["products.men_shirts", "products.women_shirts"],
    "t-shirts": ["products.men_tshirts", "products.women_tshirts"],
    "jeans": ["products.men_jeans", "products.women_jeans"],
    "trousers": ["products.men_trousers", "products.women_trousers"]
}

def extract_filters_with_krutrim(query: str):
    prompt = f'''
                User said: "{query}"
                You are a helpful assistant that extracts product filters from a user query for a fashion e-commerce site.
                Return the following fields in valid JSON:
                - gender: "men" or "women" or null
                - price_min: integer or null
                - price_max: integer or null
                - category: one of "shoes", "shirts", "t-shirts", "jeans", "trousers", or null

                Examples:
                Input: "show me men shoes between 3000 to 4000"
                Output: {{"gender": "men", "category": "shoes", "price_min": 3000, "price_max": 4000}}

                Input: "cheap women jeans"
                Output: {{"gender": "women", "category": "jeans", "price_min": null, "price_max": null}}

                Input: "lightweight running shoes under 1000 rupees"
                Output: {{"gender": null, "category": "shoes", "price_min": null, "price_max": 1000}}
'''

    try:
        response = httpx.post(
            url="https://cloud.olakrutrim.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {KRUTRIM_API_KEY}"},
            json={
                "model": "DeepSeek-R1",
                "messages": [
                    {"role": "system", "content": "You are a product filter extractor for a fashion shopping assistant."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0,
            },
            verify=False,
            timeout=60.0
        )

        if response.status_code != 200:
            print("API failed:", response.status_code, response.text)
            return {"gender": None, "category": None, "price_min": None, "price_max": None}

        output = response.json()["choices"][0]["message"]["content"]

        match = re.search(r"\{[\s\S]*?\}", output)
        if match:
            print("JSON found in output:", match.group(0))
            return json.loads(match.group(0))
        else:
            print("No JSON found in output")
            return {"gender": None, "category": None, "price_min": None, "price_max": None}

    except Exception as e:
        print("LLM parsing failed:", e)
        return {"gender": None, "category": None, "price_min": None, "price_max": None}


# Normalize embeddings if needed
def encode_query(model, query: str):
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer("all-MiniLM-L6-v2")
    vec = model.encode([query])
    return normalize(vec, axis=1).astype("float32")


def fetch_products_from_db(product_ids: list[str], category: str | None = None) -> list[dict]:
    if not product_ids:
        return []

    placeholders = ','.join([f"'{pid}'" for pid in product_ids])
    tables_to_search = CATEGORY_TABLE_MAP.get(category.lower(), []) if category else []

    # tables_to_search = CATEGORY_TABLE_MAP.get(category.lower(), [])
    if not tables_to_search:
        # Default: check all product tables if category is unknown
        tables_to_search = sum(CATEGORY_TABLE_MAP.values(), [])

    query_parts = [
        f"""
        SELECT product_id, name, price, image_urls, brand, rating, category
        FROM {table}
        WHERE product_id IN ({placeholders})
        """ for table in tables_to_search
    ]
    combined_query = " UNION ALL ".join(query_parts)

    with DBConnection.get_connection() as session:
        rows = session.execute(combined_query).fetchall()
        return [dict(row) for row in rows]


def search_semantic_products(query: str, top_k: int = 10):
    import faiss  # lazy import inside function
    from sentence_transformers import SentenceTransformer
    # Load and rebuild index dynamically
    df = pd.read_csv(EMBEDDED_PRODUCTS_CSV)
    df = df.dropna(subset=["vector_embed"]).drop_duplicates(subset=["product_id"])
    df["vector_embed"] = df["vector_embed"].apply(ast.literal_eval)
    embedding_matrix = normalize(np.vstack(df["vector_embed"].values).astype("float32"), axis=1)

    dimension = embedding_matrix.shape[1]
    index = faiss.IndexFlatIP(dimension)
    index.add(embedding_matrix)

    metadata = df[["product_id", "text_data"]]

    # Proceed with search logic
    filters = extract_filters_with_krutrim(query)
    query_vec = SentenceTransformer("all-MiniLM-L6-v2").encode([query])
    query_vec = normalize(query_vec, axis=1).astype("float32")

    scores, indices = index.search(query_vec, top_k)
    matched_ids = metadata.iloc[indices[0]]["product_id"].tolist()
    product_records = fetch_products_from_db(matched_ids, filters["category"])

    result_df = pd.DataFrame(product_records)

    if filters["gender"]:
        result_df = result_df[result_df["category"].str.lower().str.contains(filters["gender"])]
    if filters["category"]:
        result_df = result_df[result_df["category"].str.lower().str.contains(filters["category"])]
    if filters["price_min"] is not None and filters["price_max"] is not None:
        result_df = result_df[
            (result_df["price"] >= filters["price_min"]) &
            (result_df["price"] <= filters["price_max"])
        ]
    if result_df.empty:
        return []
    return result_df.head(top_k).fillna("").to_dict(orient="records")


if __name__ == "__main__":
    results = search_semantic_products("show me men shoes under 1000 rupees", 10)
    for r in results:
        print(r)