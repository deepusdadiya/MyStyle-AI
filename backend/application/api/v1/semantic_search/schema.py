from pydantic import BaseModel, Field
from typing import Optional, List, Union

class SearchRequest(BaseModel):
    query: str
    top_k: Optional[int] = 10

class ProductResponse(BaseModel):
    product_id: str
    name: Optional[str]
    price: Optional[float]
    image_urls: Optional[str]
    brand: Optional[str]
    rating: Optional[float]
    category: Optional[str]