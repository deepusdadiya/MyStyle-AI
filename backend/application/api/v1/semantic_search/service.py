import pandas as pd 
import json
import os
from sklearn.preprocessing import normalize
import numpy as np
import ast
from alchemist.postgresql.resource import DBConnection
import re
import faiss
import pandas as pd
from groq import Groq
from sqlalchemy import text
import math

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EMBEDDED_CSV = os.path.join(BASE_DIR, "..", "Semantic_Search", "embedded_products.csv")

df = pd.read_csv(EMBEDDED_CSV)
df = df.dropna(subset=["vector_embed"]).drop_duplicates(subset=["product_id"])
df["vector_embed"] = df["vector_embed"].apply(ast.literal_eval)

embedding_matrix = normalize(np.vstack(df["vector_embed"].values).astype("float32"), axis=1)
index = faiss.IndexFlatIP(embedding_matrix.shape[1])
index.add(embedding_matrix)

metadata = df[["product_id", "text_data"]]

CATEGORY_TABLE_MAP = {
    "shoes": ["products.men_shoes", "products.women_shoes"],
    "shirts": ["products.men_shirts", "products.women_shirts"],
    "t-shirts": ["products.men_tshirts", "products.women_tshirts"],
    "jeans": ["products.men_jeans", "products.women_jeans"],
    "trousers": ["products.men_trousers", "products.women_trousers"]
}

def extract_filters_with_groq(query: str):
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
        client = Groq(api_key=GROQ_API_KEY)

        response = client.chat.completions.create(
            model="deepseek-r1-distill-llama-70b",
            messages=[
                {"role": "system", "content": "You are a product filter extractor for a fashion shopping assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0,
        )

        output = response.choices[0].message.content

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


def safe_float(val):
    try:
        if isinstance(val, str):
            val = val.strip()
            if val.lower() in ["", "n/a", "nan", "none", "-"]:
                return None
        if val is None:
            return None
        num = float(val)
        if math.isnan(num) or math.isinf(num):
            return None
        return num
    except (ValueError, TypeError):
        return None

    
def fetch_products_from_db(product_ids: list[str], category: str | None = None) -> list[dict]:
    if not product_ids:
        return []

    placeholders = ','.join([f"'{pid}'" for pid in product_ids])
    tables_to_search = CATEGORY_TABLE_MAP.get(category.lower(), []) if category else []

    if not tables_to_search:
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
        rows = session.execute(text(combined_query)).mappings().fetchall()
    
    cleaned_rows = []
    for row in rows:
        row_dict = dict(row)
        row_dict["rating"] = safe_float(row_dict.get("rating", None))
        row_dict["price"] = safe_float(row_dict.get("price", None))
        row_dict["product_id"] = str(row_dict.get("product_id", ""))
        row_dict["name"] = row_dict.get("name") or ""
        row_dict["brand"] = row_dict.get("brand") or ""
        row_dict["category"] = row_dict.get("category") or ""
        row_dict["image_urls"] = row_dict.get("image_urls") or ""

        cleaned_rows.append(row_dict)
    print("🔍 FINAL CLEANED RATINGS:", [type(row["rating"]) for row in cleaned_rows])

    for row in cleaned_rows:
        print("DEBUG rating:", row["rating"], type(row["rating"]))

    for row in cleaned_rows:
        if not isinstance(row["rating"], (float, type(None))):
            print("❌ Invalid rating:", row["rating"])
    for row in cleaned_rows:
        print("✅ Validated:", row["product_id"], row["rating"], type(row["rating"]))

    return cleaned_rows


def search_semantic_products(query: str, top_k: int = 10):
    import faiss
    from sentence_transformers import SentenceTransformer

    df = pd.read_csv(EMBEDDED_CSV)
    df = df.dropna(subset=["vector_embed"]).drop_duplicates(subset=["product_id"])
    df["vector_embed"] = df["vector_embed"].apply(ast.literal_eval)
    embedding_matrix = normalize(np.vstack(df["vector_embed"].values).astype("float32"), axis=1)

    index = faiss.IndexFlatIP(embedding_matrix.shape[1])
    index.add(embedding_matrix)
    metadata = df[["product_id", "text_data"]]

    filters = extract_filters_with_groq(query)
    model = SentenceTransformer("all-MiniLM-L6-v2")
    query_vec = model.encode([query])
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

    for idx, row in result_df.iterrows():
        result_df.at[idx, "rating"] = safe_float(row.get("rating"))
        result_df.at[idx, "price"] = safe_float(row.get("price"))

        for col in ["name", "brand", "category", "image_urls"]:
            val = row.get(col)
            result_df.at[idx, col] = val if isinstance(val, str) else ""

    final_data = result_df.head(top_k).reset_index(drop=True).to_dict(orient="records")
    for row in final_data:
        for key in ["rating", "price"]:
            val = row.get(key)
            if isinstance(val, float) and (math.isnan(val) or math.isinf(val)):
                row[key] = None

    return final_data


if __name__ == "__main__":
    results = search_semantic_products("show me men shoes under 1000 rupees", 10)
    for r in results:
        print(r)