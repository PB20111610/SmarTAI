import time
import uuid
import threading
import logging
from typing import Dict, List, Any
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from backend.dependencies import get_problem_store, get_student_store
from backend.models import Correction
from backend.correct.calc import calc_node
from backend.correct.concept import concept_node
from backend.correct.proof import proof_node
from backend.correct.programming import programming_node

# Setup logger
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/ai_grading",
    tags=["ai_grading"]
)

# Store for grading results
GRADING_RESULTS = {}

class GradingRequest(BaseModel):
    student_id: str

class BatchGradingRequest(BaseModel):
    # Empty for now, but could include options for batch grading
    pass

def run_grading_task(job_id: str, student_id: str, problem_store: Dict, student_store: List):
    """Run the grading task for a specific student."""
    logger.info(f"Grading task {job_id} started for student {student_id}")
    
    try:
        # Find the student data
        student_data = None
        for student in student_store:
            if student.get("stu_id") == student_id:
                student_data = student
                break
        
        if not student_data:
            logger.error(f"Student {student_id} not found in student store")
            GRADING_RESULTS[job_id] = {
                "status": "error",
                "message": f"Student {student_id} not found"
            }
            return
        
        # Process each answer
        corrections = []
        student_answers = student_data.get("stu_ans", [])
        
        for answer in student_answers:
            q_id = answer.get("q_id")
            answer_type = answer.get("type")
            content = answer.get("content")
            
            # Get the problem rubric
            problem = problem_store.get(q_id)
            if not problem:
                logger.warning(f"Problem {q_id} not found in problem store")
                continue
                
            rubric = problem.get("criterion", "")
            max_score = 10.0  # Default max score
            
            # Prepare answer unit based on type
            answer_unit = {
                "q_id": q_id,
                "text": content
            }
            
            # Call the appropriate correction node based on question type
            try:
                if answer_type == "计算题":
                    # For calculation questions, we need to parse steps
                    # This is a simplified version - in practice, you'd extract steps from content
                    answer_unit["steps"] = [{"step_no": 1, "content": content, "formula": ""}]
                    correction = calc_node(answer_unit, rubric, max_score)
                elif answer_type == "概念题":
                    correction = concept_node(answer_unit, rubric, max_score)
                elif answer_type == "证明题":
                    correction = proof_node(answer_unit, rubric, max_score)
                elif answer_type == "编程题":
                    answer_unit["code"] = content
                    answer_unit["language"] = "python"  # Default language
                    answer_unit["test_cases"] = []  # Empty test cases for now
                    correction = programming_node(answer_unit, rubric, max_score)
                else:
                    # For other types, create a default correction
                    correction = Correction(
                        q_id=q_id,
                        type=answer_type,
                        score=5.0,
                        max_score=max_score,
                        confidence=0.5,
                        comment=f"Unsupported question type: {answer_type}",
                        steps=[]
                    )
                
                corrections.append(correction)
            except Exception as e:
                logger.error(f"Error grading question {q_id}: {e}")
                # Create a default correction for errors
                correction = Correction(
                    q_id=q_id,
                    type=answer_type,
                    score=0.0,
                    max_score=max_score,
                    confidence=0.0,
                    comment=f"Grading error: {str(e)}",
                    steps=[]
                )
                corrections.append(correction)
        
        # Store the results
        GRADING_RESULTS[job_id] = {
            "status": "completed",
            "student_id": student_id,
            "corrections": corrections
        }
        
        logger.info(f"Grading task {job_id} completed for student {student_id}")
        
    except Exception as e:
        logger.error(f"Error in grading task {job_id}: {e}")
        GRADING_RESULTS[job_id] = {
            "status": "error",
            "message": str(e)
        }


def run_batch_grading_task(job_id: str, problem_store: Dict, student_store: List):
    """Run the grading task for all students."""
    logger.info(f"Batch grading task {job_id} started for all students")
    
    try:
        # Process each student
        all_results = []
        
        for student in student_store:
            student_id = student.get("stu_id")
            if not student_id:
                continue
                
            # Process each answer for this student
            corrections = []
            student_answers = student.get("stu_ans", [])
            
            for answer in student_answers:
                q_id = answer.get("q_id")
                answer_type = answer.get("type")
                content = answer.get("content")
                
                # Get the problem rubric
                problem = problem_store.get(q_id)
                if not problem:
                    logger.warning(f"Problem {q_id} not found in problem store")
                    continue
                    
                rubric = problem.get("criterion", "")
                max_score = 10.0  # Default max score
                
                # Prepare answer unit based on type
                answer_unit = {
                    "q_id": q_id,
                    "text": content
                }
                
                # Call the appropriate correction node based on question type
                try:
                    if answer_type == "计算题":
                        # For calculation questions, we need to parse steps
                        # This is a simplified version - in practice, you'd extract steps from content
                        answer_unit["steps"] = [{"step_no": 1, "content": content, "formula": ""}]
                        correction = calc_node(answer_unit, rubric, max_score)
                    elif answer_type == "概念题":
                        correction = concept_node(answer_unit, rubric, max_score)
                    elif answer_type == "证明题":
                        correction = proof_node(answer_unit, rubric, max_score)
                    elif answer_type == "编程题":
                        answer_unit["code"] = content
                        answer_unit["language"] = "python"  # Default language
                        answer_unit["test_cases"] = []  # Empty test cases for now
                        correction = programming_node(answer_unit, rubric, max_score)
                    else:
                        # For other types, create a default correction
                        correction = Correction(
                            q_id=q_id,
                            type=answer_type,
                            score=5.0,
                            max_score=max_score,
                            confidence=0.5,
                            comment=f"Unsupported question type: {answer_type}",
                            steps=[]
                        )
                    
                    corrections.append(correction)
                except Exception as e:
                    logger.error(f"Error grading question {q_id} for student {student_id}: {e}")
                    # Create a default correction for errors
                    correction = Correction(
                        q_id=q_id,
                        type=answer_type,
                        score=0.0,
                        max_score=max_score,
                        confidence=0.0,
                        comment=f"Grading error: {str(e)}",
                        steps=[]
                    )
                    corrections.append(correction)
            
            # Add this student's results to all results
            all_results.append({
                "student_id": student_id,
                "corrections": corrections
            })
        
        # Store the results
        GRADING_RESULTS[job_id] = {
            "status": "completed",
            "results": all_results
        }
        
        logger.info(f"Batch grading task {job_id} completed for all students")
        
    except Exception as e:
        logger.error(f"Error in batch grading task {job_id}: {e}")
        GRADING_RESULTS[job_id] = {
            "status": "error",
            "message": str(e)
        }


@router.post("/grade_student/")
def start_grading(request: GradingRequest, 
                  problem_store: Dict = Depends(get_problem_store),
                  student_store: List = Depends(get_student_store)):
    """
    Start grading for a specific student.
    """
    job_id = str(uuid.uuid4())
    GRADING_RESULTS[job_id] = {"status": "pending"}
    
    # Start grading in a background thread
    thread = threading.Thread(
        target=run_grading_task, 
        args=(job_id, request.student_id, problem_store, student_store)
    )
    thread.start()
    
    return {"job_id": job_id}


@router.post("/grade_all/")
def start_batch_grading(request: BatchGradingRequest,
                       problem_store: Dict = Depends(get_problem_store),
                       student_store: List = Depends(get_student_store)):
    """
    Start grading for all students.
    """
    job_id = str(uuid.uuid4())
    GRADING_RESULTS[job_id] = {"status": "pending"}
    
    # Start grading in a background thread
    thread = threading.Thread(
        target=run_batch_grading_task, 
        args=(job_id, problem_store, student_store)
    )
    thread.start()
    
    return {"job_id": job_id}


@router.get("/grade_result/{job_id}")
def get_grading_result(job_id: str):
    """
    Get the grading result for a job.
    """
    result = GRADING_RESULTS.get(job_id, {"status": "not_found"})
    return result