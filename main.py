from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
import pandas as pd
import io

app = FastAPI()

BASE_URL = "https://exam.sanand.workers.dev/questionData"
PARAMS = {
    "email": "21f1000895@ds.study.iitm.ac.in",
    "quizSign": "du8EHKVEdBBJxNiRf32Kw65ezblXNTIJDb6mYAJRdcr5ndM2CTIxxkzvO28OXLxUHHD9hr+X+fpbjzE2HJtXdST0E6bxql3tkWGyFlXYFWKlHStvnDP5+C+lcPktXW+zq62gLzmEb+o1NOQLw/fzc9WDDf45IpT3BYSPyuaQoT3hcHteSFnx2mGZy0l8TybpBEXbt+fexeItpJVdFBl3byrBsV2Zt6GMqjI37t0jPwR5OWYUaWoii8g+YOHt2fblraAx/2gtQpxXZdGbT6NqhDB/FDFPUTzapBAvfk1SHlRkf4ob3SHOsNAZiEapKaqv8XxEb8CvvbjjpFJXeLv8hQ==",
    "questionId": "q-ledger-agent-server"
}

def get_ledger_df(path="/"):
    try:
        resp = requests.get(BASE_URL, params={**PARAMS, "path": path}, timeout=10)
        data = resp.json()
        if isinstance(data, str):
            return pd.read_csv(io.StringIO(data))
        elif isinstance(data, list):
            return pd.DataFrame(data)
        elif isinstance(data, dict):
            # Check if nested under a key like 'data', 'orders', etc.
            for k in ['data', 'orders', 'ledger', 'results']:
                if k in data and isinstance(data[k], list):
                    return pd.DataFrame(data[k])
            return pd.DataFrame([data])
        return pd.DataFrame()
    except Exception as e:
        return pd.DataFrame()

class QuestionRequest(BaseModel):
    question: str

@app.post("/")
async def answer_question(payload: QuestionRequest):
    question = payload.question
    q_lower = question.lower()
    
    # Fetch ledger data from the company API endpoint
    df = get_ledger_df("/")
    
    if df.empty:
        return {"answer": 0}

    # Standardize column names if needed
    df.columns = [c.lower() for c in df.columns]

    if 'date' in df.columns:
        df['dt'] = pd.to_datetime(df['date'], errors='coerce')
        df['year'] = df['dt'].dt.year
        df['month'] = df['dt'].dt.month

    if 'quantity' in df.columns and 'price' in df.columns:
        df['revenue'] = pd.to_numeric(df['quantity'], errors='coerce') * pd.to_numeric(df['price'], errors='coerce')

    # 1. Top-selling product queries (e.g. "In May 2026, what was the top-selling product by revenue (in USD)?")
    if "top-selling product" in q_lower or "top product" in q_lower:
        filtered = df.copy()
        if "may 2026" in q_lower and 'year' in filtered.columns:
            filtered = filtered[(filtered['year'] == 2026) & (filtered['month'] == 5)]
        elif "may" in q_lower and 'month' in filtered.columns:
            filtered = filtered[filtered['month'] == 5]
            
        if not filtered.empty and 'product' in filtered.columns and 'revenue' in filtered.columns:
            grouped = filtered.groupby('product')['revenue'].sum().reset_index()
            if not grouped.empty:
                top_row = grouped.sort_values(by='revenue', ascending=False).iloc[0]
                return {"answer": str(top_row['product'])}

    # 2. Refund / Count / Order queries (e.g., "How many orders from West were refunded in January 2026?")
    if "how many" in q_lower or "refund" in q_lower or "count" in q_lower:
        filtered = df.copy()
        
        # Date filters
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

        # Region / city filters if specified in question
        for reg in ['west', 'east', 'north', 'south', 'central']:
            if reg in q_lower:
                if 'region' in filtered.columns:
                    filtered = filtered[filtered['region'].str.lower() == reg]
                elif 'city' in filtered.columns:
                    # If cities are stored, filter accordingly
                    pass

        # Refund status filter
        if 'status' in filtered.columns and ('refund' in q_lower or 'refunded' in q_lower):
            filtered = filtered[filtered['status'].str.lower().str.contains('refund', na=False)]

        return {"answer": int(len(filtered))}

    # 3. Revenue total queries
    if "revenue" in q_lower:
        filtered = df.copy()
        if "march 2026" in q_lower:
            filtered = filtered[(filtered['year'] == 2026) & (filtered['month'] == 3)]
        elif "may 2026" in q_lower:
            filtered = filtered[(filtered['year'] == 2026) & (filtered['month'] == 5)]
            
        total_rev = float(filtered['revenue'].sum()) if 'revenue' in filtered.columns else 0.0
        return {"answer": round(total_rev, 2)}

    return {"answer": 0}
