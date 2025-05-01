import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"
import asyncio
import nest_asyncio
nest_asyncio.apply()
import streamlit as st
import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.preprocessing import normalize
import faiss
import ast
from Semantic_Search.semantic_search import extract_filters_with_llm
import warnings
warnings.filterwarnings("ignore", category=UserWarning)

# Load everything
@st.cache_resource
def load_resources():
    from sentence_transformers import SentenceTransformer  # 👈 move inside
    import faiss
    import pandas as pd

    model = SentenceTransformer("all-MiniLM-L6-v2")
    index = faiss.read_index("Semantic_Search/faiss_product_index.index")
    metadata = pd.read_csv("Semantic_Search/faiss_metadata.csv")
    full_data = pd.concat([
        pd.read_csv(file) for file in [
            "Data/products/men_shoes.csv", "Data/products/men_shirts.csv", "Data/products/men_t-shirts.csv", "Data/products/men_jeans.csv", "Data/products/men_trousers.csv",
            "Data/products/women_shoes.csv", "Data/products/women_shirts.csv", "Data/products/women_t-shirts.csv", "Data/products/women_jeans.csv", "Data/products/women_trousers.csv"
        ]
    ])
    return model, index, metadata, full_data


model, index, metadata, full_data = load_resources()

# Semantic Search
# def search_products(query, top_k=20):
#     query_vec = model.encode([query])
#     query_vec = normalize(query_vec, axis=1).astype("float32")
#     scores, indices = index.search(query_vec, top_k)
#     return metadata.iloc[indices[0]]

def search_products(query, top_k=30):
    filters = extract_filters_with_llm(query)
    gender = filters["gender"]
    category = filters["category"]
    price_min = filters["price_min"]
    price_max = filters["price_max"]

    query_vec = model.encode([query])
    query_vec = normalize(query_vec, axis=1).astype("float32")
    scores, indices = index.search(query_vec, top_k)

    results = metadata.iloc[indices[0]].copy()
    results = results.merge(full_data, on="product_id", how="left")

    if gender:
        results = results[results["category"].str.lower().str.contains(gender)]
    if category:
        results = results[results["category"].str.lower().str.contains(category)]
    if price_min is not None and price_max is not None:
        results = results[
            results["price"].apply(lambda x: isinstance(x, (int, float))) &
            (results["price"] >= price_min) & (results["price"] <= price_max)
        ]
    return results.head(20)

# UI
# st.set_page_config(page_title="SmartShop: Semantic Search", layout="wide")
st.title("🛍️ SmartShop: Semantic Product Search")

query = st.text_input("What are you looking for?", placeholder="e.g., casual red shoes under ₹1500")

if query:
    results = search_products(query)
    st.subheader("🔍 Top Matching Products")
    for _, row in results.iterrows():
        match = full_data[full_data["product_id"] == row["product_id"]]
        if match.empty:
            st.warning(f"Product ID {row['product_id']} not found in product CSVs.")
            continue  # Skip to next
        product_row = match.iloc[0]
        # Layout
        col1, col2 = st.columns([1, 3])
        with col1:
            image_urls = str(product_row.get("image_urls", "")).split("|")
            first_image_url = image_urls[0].strip() if image_urls else None
            if first_image_url and first_image_url.startswith("https"):
                st.image(first_image_url, width=160)
            else:
                st.markdown("🖼️ *No Image Available*")
        with col2:
            st.markdown(f"### {product_row['name']}")
            st.markdown(f"💬 **Description**: {product_row['description'][:300]}...")
            st.markdown(f"💰 **Price**: ₹{product_row['price']}")
            st.markdown(f"⭐ **Rating**: {product_row['rating']}")
            st.markdown("---")


if __name__ == "__main__":
    import nest_asyncio
    nest_asyncio.apply()
    import warnings
    warnings.filterwarnings("ignore", category=UserWarning)
    os.environ["TOKENIZERS_PARALLELISM"] = "false"