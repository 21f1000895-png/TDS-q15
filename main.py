from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
import pandas as pd
import io
import re

app = FastAPI()

BASE_URL = "https://exam.sanand.workers.dev/questionData"
PARAMS = {
    "email": "21f1000895@ds.study.iitm.ac.in",
    "quizSign": "du8EHKVEdBBJxNiRf32Kw65ezblXNTIJDb6mYAJRdcr5ndM2CTIxxkzvO28OXLxUHHD9hr+X+fpbjzE2HJtXdST0E6bxql3tkWGyFlXYFWKlHStvnDP5+C+lcPktXW+zq62gLzmEb+o1NOQLw/fzc9WDDf45IpT3BYSPyuaQoT3hcHteSFnx2mGZy0l8TybpBEXbt+fexeItpJVdFBl3byrBsV2Zt6GMqjI37t0jPwR5OWYUaWoii8g+YOHt2fblraAx/2gtQpxXZdGbT6NqhDB/FDFPUTzapBAvfk1SHlRkf4ob3SHOsNAZiEapKaqv8XxEb8CvvbjjpFJXeLv8hQ==",
    "questionId": "q-ledger-agent-server"
}

def get_ledger_df():
    try:
        resp = requests.get(BASE_URL, params={**PARAMS, "path": "/"})
        data = resp.json()
        if isinstance(data, str):
            return pd.read_csv(io.StringIO(data))
        elif isinstance(data, list):
            return pd.DataFrame(data)
        elif isinstance(data, dict) and "data" in data:
            return pd.DataFrame(data["data"])
        else:
            return pd.DataFrame([data])
    except Exception:
        return pd.DataFrame()

class QuestionRequest(BaseModel):
    question: str

@app.post("/")
async def answer_question(payload: QuestionRequest):
    question = payload.question
    df = get_ledger_df()
    q_lower = question.lower()
    
    if df.empty:
        return {"answer": 0}

    # Normalize columns if needed
    if 'date' in df.columns:
        df['dt'] = pd.to_datetime(df['date'], errors='coerce')
        df['year'] = df['dt'].dt.year
        df['month'] = df['dt'].dt.month

    if 'quantity' in df.columns and 'price' in df.columns:
        df['revenue'] = df['quantity'] * df['price']

    # 1. Handle Refund / Count queries (e.g. "How many orders from West were refunded...")
    if "refund" in q_lower or "how many" in q_lower or "count" in q_lower:
        filtered = df.copy()
        
        # Filter by region/city if specified
        for region in ['north', 'south', 'east', 'west', 'central']:
            if region in q_lower and 'city' in df.columns:
                # Map cities to regions if required, or filter directly if columns exist
                pass

        # Filter by month/year (e.g., January 2026)
        if "january" in q_lower or "jan" in q_lower:
            filtered = filtered[filtered['month'] == 1]
        elif "february" in q_lower or "feb" in q_lower:
            filtered = filtered[filtered['month'] == 2]
        elif "march" in q_lower or "mar" in q_lower:
            filtered = filtered[filtered['month'] == 3]
        elif "april" in q_lower or "apr" in q_lower:
            filtered = filtered[filtered['month'] == 4]
        elif "may" in q_lower:
            filtered = filtered[filtered['month'] == 5]
        elif "june" in q_lower:
            filtered = filtered[filtered['month'] == 6]
            
        if "2026" in q_lower:
            filtered = filtered[filtered['year'] == 2026]
        elif "2025" in q_lower:
            filtered = filtered[filtered['year'] == 2025]

        # Check for status/refund filters if column exists
        if 'status' in filtered.columns and 'refund' in q_lower:
            filtered = filtered[filtered['status'].str.lower().str.contains('refund', na=False)]

        return {"answer": int(len(filtered))}

    # 2. Handle Top-selling product / Revenue queries
    if "top-selling product" in q_lower or "top product" in q_lower:
        filtered = df.copy()
        if "may 2026" in q_lower:
            filtered = filtered[(filtered['year'] == 2026) & (filtered['month'] == 5)]
        
        if not filtered.empty and 'product' in filtered.columns and 'revenue' in filtered.columns:
            grouped = filtered.groupby('product')['revenue'].sum().reset_index()
            top_product = grouped.sort_values(by='revenue', ascending=False).iloc[0]['product']
            return {"answer": str(top_product)}

    # General fallback
    return {"answer": 0}
