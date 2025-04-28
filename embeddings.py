from sentence_transformers import SentenceTransformer
import pandas as pd
import glob

# Step 1: Load all product files
csv_files = glob.glob("data/products/*.csv")  # adjust to your local folder
product_dataframes = []

# Load only product-related files
for file in csv_files:
    if any(skip in file for skip in ["user_interactions", "orders & support data", "customer_reviews", "embedded_products"]):
        continue
    df = pd.read_csv(file, on_bad_lines='skip')
    print(file)
    if "product_id" in df.columns and "name" in df.columns and "description" in df.columns:
        product_dataframes.append(df[["product_id", "name", "description"]])

merged_df = pd.concat(product_dataframes, ignore_index=True)
merged_df["text_data"] = merged_df["name"].fillna("") + " " + merged_df["description"].fillna("")
merged_df = merged_df[merged_df["text_data"].notnull() & (merged_df["text_data"].str.strip() != "")]

# Step 2: Generate embeddings
model = SentenceTransformer("all-MiniLM-L6-v2")
embeddings = model.encode(merged_df["text_data"].tolist(), show_progress_bar=True)

# Step 3: Save output
merged_df["vector_embed"] = embeddings.tolist()
merged_df[["product_id", "text_data", "vector_embed"]].to_csv("embedded_products.csv", index=False)

print("Embedded_products.csv generated successfully")
total_loaded = sum(len(pd.read_csv(f)) for f in csv_files)
print("🧾 Total raw records:", total_loaded)
print("✅ Unique product_ids after merge:", len(merged_df))
print("🧼 Non-empty text_data:", merged_df['text_data'].str.strip().ne("").sum())