from fastapi import FastAPI, Depends, HTTPException, Body
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
import os

from backend.database import get_db, Question, TestCase
from backend.parser import parse_prompt
from backend.executor import run_code

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Pydantic Models ---
class TestCaseCreate(BaseModel):
    input_data: str
    expected_output: str
    is_sample: bool = True

class QuestionCreate(BaseModel):
    title: str
    description: str
    constraints: str
    time_limit_ms: int = 1000
    test_cases: List[TestCaseCreate] = []

class ParseRequest(BaseModel):
    prompt: str

class RunRequest(BaseModel):
    language: str
    code: str

# --- API Routes ---

@app.post("/api/parse-question")
def api_parse_question(req: ParseRequest):
    return parse_prompt(req.prompt)

@app.post("/api/questions")
def create_question(q: QuestionCreate, db: Session = Depends(get_db)):
    db_question = Question(
        title=q.title,
        description=q.description,
        constraints=q.constraints,
        time_limit_ms=q.time_limit_ms
    )
    db.add(db_question)
    db.commit()
    db.refresh(db_question)

    for tc in q.test_cases:
        db_tc = TestCase(
            question_id=db_question.id,
            input_data=tc.input_data,
            expected_output=tc.expected_output,
            is_sample=tc.is_sample
        )
        db.add(db_tc)
    
    db.commit()
    return {"message": "Question created successfully", "question_id": db_question.id}

@app.get("/api/questions")
def get_questions(db: Session = Depends(get_db)):
    questions = db.query(Question).all()
    return [{"id": q.id, "title": q.title} for q in questions]

@app.get("/api/questions/{q_id}")
def get_question(q_id: int, db: Session = Depends(get_db)):
    q = db.query(Question).filter(Question.id == q_id).first()
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")
    
    test_cases = db.query(TestCase).filter(TestCase.question_id == q_id).all()
    return {
        "id": q.id,
        "title": q.title,
        "description": q.description,
        "constraints": q.constraints,
        "time_limit_ms": q.time_limit_ms,
        "test_cases": [{"input": tc.input_data, "expected_output": tc.expected_output} for tc in test_cases]
    }

@app.post("/api/questions/{q_id}/run")
def run_solution(q_id: int, req: RunRequest, db: Session = Depends(get_db)):
    q = db.query(Question).filter(Question.id == q_id).first()
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")
    
    test_cases = db.query(TestCase).filter(TestCase.question_id == q_id).all()
    if not test_cases:
        return {"status": "Error", "message": "No test cases found for this question."}

    results = []
    all_passed = True

    for i, tc in enumerate(test_cases):
        res = run_code(req.language, req.code, tc.input_data, q.time_limit_ms)
        
        # Determine if answer matches
        actual_output = res["output"].strip()
        expected = tc.expected_output.strip()
        passed = False
        
        if res["status"] == "Success":
            if actual_output == expected:
                passed = True
            else:
                passed = False
                all_passed = False
        else:
            all_passed = False

        results.append({
            "test_case": i + 1,
            "status": res["status"],
            "passed": passed,
            "time_taken_ms": res["time_taken_ms"],
            "expected_output": expected,
            "actual_output": actual_output,
            "error": res["error"]
        })

    return {
        "overall_status": "Accepted" if all_passed else "Rejected",
        "results": results
    }

# Mount static files for frontend
# Make sure frontend folder exists
os.makedirs("frontend", exist_ok=True)
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
