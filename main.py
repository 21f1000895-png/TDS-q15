from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
import pandas as pd

app = FastAPI()

# Base ledger API URL and credentials
BASE_URL = "https://exam.sanand.workers.dev/questionData"
PARAMS = {
    "email": "21f1000895@ds.study.iitm.ac.in",
    "quizSign": "du8EHKVEdBBJxNiRf32Kw65ezblXNTIJDb6mYAJRdcr5ndM2CTIxxkzvO28OXLxUHHD9hr+X+fpbjzE2HJtXdST0E6bxql3tkWGyFlXYFWKlHStvnDP5+C+lcPktXW+zq62gLzmEb+o1NOQLw/fzc9WDDf45IpT3BYSPyuaQoT3hcHteSFnx2mGZy0l8TybpBEXbt+fexeItpJVdFBl3byrBsV2Zt6GMqjI37t0jPwR5OWYUaWoii8g+YOHt2fblraAx/2gtQpxXZdGbT6NqhDB/FDFPUTzapBAvfk1SHlRkf4ob3SHOsNAZiEapKaqv8XxEb8CvvbjjpFJXeLv8hQ==",
    "questionId": "q-ledger-agent-server"
}

# Cache for data
ledger_data = None

def fetch_ledger_data():
    global ledger_data
    if ledger_data is not None:
        return ledger_data
    
    try:
        # Fetch root path or endpoints
        resp = requests.get(BASE_URL, params={**PARAMS, "path": "/"})
        data = resp.json()
        ledger_data = data
        return data
    except Exception as e:
        return {"error": str(e)}

@app.on_event("startup")
async def startup_event():
    fetch_ledger_data()

class QuestionRequest(BaseModel):
    question: str

@app.post("/")
async def answer_question(payload: QuestionRequest):
    q = payload.question.lower()
    data = fetch_ledger_data()
    
    # Example logic / rule-based fallback or LLM integration
    # You can parse questions about revenue, refunds, products, etc., using Pandas on your loaded data.
    
    # Placeholder example:
    return {"answer": "Processed successfully"}