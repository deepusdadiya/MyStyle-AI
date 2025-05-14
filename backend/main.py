import multiprocessing

if __name__ == "__main__":
    multiprocessing.set_start_method("fork")
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from application.api.v1.semantic_search.router import router as semantic_router
# from application.api.product_recommendation.router import router as recommendation_router

app = FastAPI(
    title="MyStyle-AI Backend",
    version="1.0",
    description="FastAPI backend for AI-based semantic search and recommendations"
)

# Enable CORS so frontend (e.g., Streamlit) can call API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # You can restrict this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API modules
app.include_router(semantic_router, prefix="/api/v1/semantic-search", tags=["Semantic Search"])
# app.include_router(recommendation_router, prefix="/api/v1/recommendations", tags=["Recommendations"])

# Root healthcheck
@app.get("/", tags=["Health"])
def root():
    return {"message": "MyStyle-AI API is running"}