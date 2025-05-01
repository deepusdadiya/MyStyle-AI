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
df = df.dropna(subset=["vector_embed"])      # Drop rows with NaN in vector_embed
df = df.drop_duplicates(subset=["product_id"], keep="first")

# Converting stringified vectors into actual lists
df["vector_embed"] = df["vector_embed"].apply(ast.literal_eval)    # Convert string to list
embedding_matrix = np.vstack(df["vector_embed"].values).astype("float32")     # Convert to float32 for FAISS

# Normalize embeddings for cosine similarity
embedding_matrix = normalize(embedding_matrix, axis=1)    # Normalize the embedding matrix

# Create FAISS index
dimension = embedding_matrix.shape[1]   # Dimension of the embedding vectors
index = faiss.IndexFlatIP(dimension)  # IP = Inner Product (for cosine)
index.add(embedding_matrix)    # Add the vectors to the index

# Save index + metadata
faiss.write_index(index, "Semantic_Search/faiss_product_index.index")    # Save the FAISS index
df[["product_id", "text_data"]].to_csv("Semantic_Search/faiss_metadata.csv", index=False)    # Save metadata

print("FAISS index and metadata saved.")