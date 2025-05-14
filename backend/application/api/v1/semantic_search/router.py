from fastapi import APIRouter
from application.api.v1.semantic_search.schema import SearchRequest, ProductResponse
from application.api.v1.semantic_search.service import search_semantic_products

router = APIRouter()

@router.post("/search", response_model=list[ProductResponse])
def semantic_product_search(payload: SearchRequest):
    return search_semantic_products(query=payload.query, top_k=payload.top_k)