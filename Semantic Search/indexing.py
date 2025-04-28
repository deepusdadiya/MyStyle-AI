import pandas as pd
import faiss
import numpy as np
from sklearn.preprocessing import normalize
import ast
import glob
import os
print(os.getcwd())  # Shows current working directory
print(os.listdir("Data"))  # Lists contents of folder

df = pd.read_csv("Data/embedded_products.csv")

# Load the embedded products CSV
df = pd.read_csv("Data/embedded_products.csv")
df = df.dropna(subset=["vector_embed"])

# Converting stringified vectors into actual lists
df["vector_embed"] = df["vector_embed"].apply(ast.literal_eval)
embedding_matrix = np.vstack(df["vector_embed"].values).astype("float32")

# Normalize embeddings for cosine similarity
embedding_matrix = normalize(embedding_matrix, axis=1)

# Create FAISS index
dimension = embedding_matrix.shape[1]
index = faiss.IndexFlatIP(dimension)  # IP = Inner Product (for cosine)
index.add(embedding_matrix)

# Save index + metadata
faiss.write_index(index, "Semantic Search/faiss_product_index.index")
df[["product_id", "text_data"]].to_csv("Semantic Search/faiss_metadata.csv", index=False)

print("FAISS index and metadata saved.")