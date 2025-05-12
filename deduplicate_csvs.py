import pandas as pd
import os

input_dir = "Data/products"
output_dir = "Data/deduped"

os.makedirs(output_dir, exist_ok=True)

category_files = [
    "men_shoes.csv", "men_shirts.csv", "men_t-shirts.csv", "men_jeans.csv", "men_trousers.csv",
    "women_shoes.csv", "women_shirts.csv", "women_t-shirts.csv", "women_jeans.csv", "women_trousers.csv"
]


for filename in category_files:
    input_path = os.path.join(input_dir, filename)
    output_path = os.path.join(output_dir, f"deduped_{filename}")
    
    df = pd.read_csv(input_path)
    df_cleaned = df.drop_duplicates(subset=["product_id"], keep="first")
    df_cleaned.to_csv(output_path, index=False)
    print(f"✅ Deduplicated: {filename} → {output_path}")