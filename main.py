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
            for k in ['data', 'orders', 'ledger', 'results', 'items']:
                if k in data and isinstance(data[k], list):
                    return pd.DataFrame(data[k])
            return pd.DataFrame([data])
        return pd.DataFrame()
    except Exception:
        return pd.DataFrame()

class QuestionRequest(BaseModel):
    question: str

@app.post("/")
async def answer_question(payload: QuestionRequest):
    question = payload.question
    q_lower = question.lower()
    
    df = get_ledger_df("/")
    if df.empty:
        return {"answer": 0}

    # Normalize column names to lowercase
    df.columns = [c.lower() for c in df.columns]

    # Date parsing
    if 'date' in df.columns:
        df['dt'] = pd.to_datetime(df['date'], errors='coerce')
        df['year'] = df['dt'].dt.year
        df['month'] = df['dt'].dt.month

    # Revenue calculation
    if 'quantity' in df.columns and 'price' in df.columns:
        df['revenue'] = pd.to_numeric(df['quantity'], errors='coerce') * pd.to_numeric(df['price'], errors='coerce')

    # 1. Distinct customer queries (e.g., "How many different customers placed at least one paid order for a Toaster?")
    if "customer" in q_lower or "customers" in q_lower:
        filtered = df.copy()
        
        # Filter by product if mentioned in question
        for col in ['product', 'item', 'product_name']:
            if col in filtered.columns:
                for prod in filtered[col].dropna().unique():
                    if str(prod).lower() in q_lower:
                        filtered = filtered[filtered[col].astype(str).str.lower() == str(prod).lower()]
                        break

        # Filter by status (paid / completed) if status column exists
        for status_col in ['status', 'order_status', 'type']:
            if status_col in filtered.columns and ('paid' in q_lower or 'completed' in q_lower):
                filtered = filtered[filtered[status_col].astype(str).str.lower().str.contains('paid|complete', na=False)]

        # Count unique customers
        cust_col = None
        for c in ['customer', 'customer_id', 'client', 'email', 'user_id']:
            if c in filtered.columns:
                cust_col = c
                break
        
        if cust_col:
            return {"answer": int(filtered[cust_col].nunique())}
        else:
            return {"answer": int(len(filtered))}

    # 2. Top-selling product queries
    if "top-selling product" in q_lower or "top product" in q_lower:
        filtered = df.copy()
        if not filtered.empty and 'product' in filtered.columns and 'revenue' in filtered.columns:
            grouped = filtered.groupby('product')['revenue'].sum().reset_index()
            if not grouped.empty:
                top_row = grouped.sort_values(by='revenue', ascending=False).iloc[0]
                return {"answer": str(top_row['product'])}

    # 3. Refund / Count queries
    if "how many" in q_lower or "refund" in q_lower or "count" in q_lower:
        filtered = df.copy()
        if 'status' in filtered.columns and 'refund' in q_lower:
            filtered = filtered[filtered['status'].astype(str).str.lower().str.contains('refund', na=False)]
        return {"answer": int(len(filtered))}

    # 4. Revenue total queries
    if "revenue" in q_lower:
        filtered = df.copy()
        total_rev = float(filtered['revenue'].sum()) if 'revenue' in filtered.columns else 0.0
        return {"answer": round(total_rev, 2)}

    return {"answer": 0}
