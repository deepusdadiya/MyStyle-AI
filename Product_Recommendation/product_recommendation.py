import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

interactions_df = pd.read_csv("Data/user_interactions.csv")

filtered_df = interactions_df[interactions_df["action_type"].isin(["view", "purchase"])]

interaction_matrix = pd.crosstab(filtered_df["user_id"], filtered_df["product_id"])

# Calculate cosine similarity between products
similarity_matrix = pd.DataFrame(
    cosine_similarity(interaction_matrix.T),
    index=interaction_matrix.columns,
    columns=interaction_matrix.columns
)

# Define the recommendation function
def recommend_similar_products(product_id, top_k=5):
    if product_id not in similarity_matrix.columns:
        return []
    similar_scores = similarity_matrix[product_id].drop(index=product_id).sort_values(ascending=False)
    print(f"Similar scores for product {product_id}:\n{similar_scores}")
    return similar_scores.head(top_k).index.tolist()

# Example usage:
example_product = filtered_df["product_id"].iloc[0]
print(f"People who viewed this product ({example_product}) also viewed:")
print(recommend_similar_products(example_product, top_k=5))