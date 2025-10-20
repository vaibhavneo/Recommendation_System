# api.py (FastAPI)
from fastapi import FastAPI

app = FastAPI()

@app.get("/health")
def health():
    return {"ok": True}

@app.get("/recommend/{user_id}")
def recommend(user_id: int, k: int = 5):
    return {"user": user_id, "items": [101, 102, 103, 104, 105][:k]}

# Optional if you implement item-to-item
@app.get("/similar/{item_id}")
def similar(item_id: int, k: int = 5):
    return {"item": item_id, "items": [201, 202, 203, 204, 205][:k]}
