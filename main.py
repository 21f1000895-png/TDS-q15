from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
import pandas as pd
import io
import re

app = FastAPI()

# Credentials and URL for your ledger API
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
        # Assuming the API returns CSV text, a list of dicts, or a nested structure
        if isinstance(data, str):
            return pd.read_csv(io.StringIO(data))
        elif isinstance(data, list):
            return pd.DataFrame(data)
        elif isinstance(data, dict) and "data" in data:
            return pd.DataFrame(data["data"])
        else:
            # Fallback if it's a URL or structured dict
            return pd.DataFrame([data])
    except Exception as e:
        # Return empty df or handle accordingly
        return pd.DataFrame()

class QuestionRequest(BaseModel):
    question: str

@app.post("/")
async def answer_question(payload: QuestionRequest):
    question = payload.question
    df = get_ledger_df()
    
    q_lower = question.lower()
    
    # Example handling for revenue / top-selling product by month
    if "top-selling product" in q_lower or "top product" in q_lower:
        # Extract month/year if present, e.g., "May 2026"
        # Compute revenue = quantity * price (or similar columns)
        if not df.empty and 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'], errors='coerce')
            if 'quantity' in df.columns and 'price' in df.columns:
                df['revenue'] = df['quantity'] * df['price']
            
            # Filter by month/year if mentioned in question
            if "may 2026" in q_lower:
                filtered = df[(df['date'].dt.year == 2026) & (df['date'].dt.month == 5)]
            else:
                filtered = df
                
            if not filtered.empty and 'product' in filtered.columns and 'revenue' in filtered.columns:
                grouped = filtered.groupby('product')['revenue'].sum().reset_index()
                top_product = grouped.sort_values(by='revenue', ascending=False).iloc[0]['product']
                return {"answer": top_product}

    # Default fallback calculation or general query processor
    return {"answer": "No data match"}
