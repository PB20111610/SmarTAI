import time
import uuid
import threading
import logging
import concurrent.futures
from typing import Dict, List, Any
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from functools import lru_cache

from backend.dependencies import get_problem_store, get_student_store, get_llm
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

# Add a function to get all job IDs for debugging
def get_all_job_ids():
    return list(GRADING_RESULTS.keys())

# Cache for LLM clients to avoid repeated initialization
LLM_CLIENT_CACHE = {}

# Cache for processed rubrics to avoid redundant processing
RUBRIC_CACHE = {}

# Cache for processed rubrics to avoid redundant processing
@lru_cache(maxsize=128)
def get_processed_rubric(q_id: str, rubric_text: str) -> str:
    """Cache processed rubrics to avoid redundant processing."""
    # In a real implementation, this could do more complex processing
    # For now, we just return the rubric as-is but cache it
    return rubric_text

class GradingRequest(BaseModel):
    student_id: str

class BatchGradingRequest(BaseModel):
    # Empty for now, but could include options for batch grading
    pass

def get_cached_llm():
    """Get a cached LLM client instance to avoid repeated initialization."""
    thread_id = threading.get_ident()
    if thread_id not in LLM_CLIENT_CACHE:
        # Import here to avoid circular imports
        from langchain_openai import ChatOpenAI
        import os
        OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "8dcdf3e9238f48f4ae329f638e66dfe2.HHIbfrj5M4GcjM8f")
        OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://open.bigmodel.cn/api/paas/v4")
        OPENAI_MODEL = os.getenv("OPENAI_MODEL", "glm-4")
        
        LLM_CLIENT_CACHE[thread_id] = ChatOpenAI(
            model=OPENAI_MODEL,
            temperature=0.0,
            api_key=OPENAI_API_KEY,
            base_url=OPENAI_API_BASE,
        )
    return LLM_CLIENT_CACHE[thread_id]

def process_student_answer(answer: Dict[str, Any], problem_store: Dict[str, Any]) -> Correction:
    """Process a single student answer and return the correction result."""
    q_id = answer.get("q_id")
    answer_type = answer.get("type")
    content = answer.get("content")
    
    # Get the problem rubric
    problem = problem_store.get(q_id)
    if not problem:
        logger.warning(f"Problem {q_id} not found in problem store")
        # Create a default correction for missing problems
        return Correction(
            q_id=q_id,
            type=answer_type or "概念题",
            score=0.0,
            max_score=10.0,
            confidence=0.0,
            comment=f"Problem {q_id} not found",
            steps=[]
        )
        
    # Use cached rubric processing
    rubric_raw = problem.get("criterion", "")
    rubric = get_processed_rubric(q_id, rubric_raw)
    max_score = 10.0  # Default max score
    
    # Prepare answer unit based on type
    answer_unit = {
        "q_id": q_id,
        "text": content
    }
    
    # Map Chinese question types to internal English types for processing
    type_mapping = {
        "概念题": "concept",
        "计算题": "calculation", 
        "证明题": "proof",
        "编程题": "programming"
    }
    
    # Get internal type for processing
    internal_type = type_mapping.get(answer_type, "concept")
    
    # Get cached LLM client
    llm = get_cached_llm()
    
    # Call the appropriate correction node based on question type
    try:
        if internal_type == "calculation":
            # For calculation questions, we need to parse steps
            # This is a simplified version - in practice, you'd extract steps from content
            answer_unit["steps"] = [{"step_no": 1, "content": content, "formula": ""}]
            # Ensure steps are properly formatted for calc_node
            if not isinstance(answer_unit["steps"], list) or len(answer_unit["steps"]) == 0:
                answer_unit["steps"] = [{"step_no": 1, "content": content, "formula": ""}]
            elif not isinstance(answer_unit["steps"][0], dict) or "step_no" not in answer_unit["steps"][0]:
                answer_unit["steps"] = [{"step_no": 1, "content": content, "formula": ""}]
            correction = calc_node(answer_unit, rubric, max_score, llm)
            # Ensure the type in the correction is the original Chinese type
            correction.type = answer_type
            return correction
        elif internal_type == "concept":
            # Ensure answer_unit has required fields for concept_node
            if "text" not in answer_unit:
                answer_unit["text"] = content
            if "q_id" not in answer_unit:
                answer_unit["q_id"] = q_id
            correction = concept_node(answer_unit, rubric, max_score, llm)
            # Ensure the type in the correction is the original Chinese type
            correction.type = answer_type
            return correction
        elif internal_type == "proof":
            # For proof questions, we need to parse steps from content
            # This is a simplified version - in practice, you'd extract actual proof steps
            answer_unit["steps"] = [{"step_no": 1, "content": content}]
            # Ensure steps are properly formatted for proof_node
            # The proof_node expects ProofStep objects, not dictionaries
            if not isinstance(answer_unit["steps"], list) or len(answer_unit["steps"]) == 0:
                answer_unit["steps"] = [{"step_no": 1, "content": content}]
            elif not isinstance(answer_unit["steps"][0], dict) or "step_no" not in answer_unit["steps"][0]:
                answer_unit["steps"] = [{"step_no": 1, "content": content}]
            correction = proof_node(answer_unit, rubric, max_score, llm)
            # Ensure the type in the correction is the original Chinese type
            correction.type = answer_type
            return correction
        elif internal_type == "programming":
            answer_unit["code"] = content
            answer_unit["language"] = "python"  # Default language
            answer_unit["test_cases"] = []  # Empty test cases for now
            # Ensure all required fields are properly formatted for programming_node
            if not isinstance(answer_unit["test_cases"], list):
                answer_unit["test_cases"] = []
            if "code" not in answer_unit:
                answer_unit["code"] = content
            if "language" not in answer_unit:
                answer_unit["language"] = "python"
            correction = programming_node(answer_unit, rubric, max_score, llm)
            # Ensure the type in the correction is the original Chinese type
            correction.type = answer_type
            return correction
        else:
            # For other types, create a default correction
            return Correction(
                q_id=q_id,
                type=answer_type,
                score=5.0,
                max_score=max_score,
                confidence=0.5,
                comment=f"Unsupported question type: {answer_type}",
                steps=[]
            )
    except Exception as e:
        logger.error(f"Error grading question {q_id}: {e}")
        # Create a default correction for errors
        return Correction(
            q_id=q_id,
            type=answer_type,
            score=0.0,
            max_score=max_score,
            confidence=0.0,
            comment=f"Grading error: {str(e)}",
            steps=[]
        )

def process_student_submission(student: Dict[str, Any], problem_store: Dict[str, Any]) -> Dict[str, Any]:
    """Process all answers for a single student and return the results."""
    student_id = student.get("stu_id")
    if not student_id:
        return None
        
    logger.info(f"Processing submission for student {student_id}")
    
    # Process each answer for this student in parallel
    corrections = []
    student_answers = student.get("stu_ans", [])
    
    # Use ThreadPoolExecutor to process answers in parallel for each student
    # Increased max_workers for better parallelization
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        # Submit all answer processing tasks
        future_to_answer = {
            executor.submit(process_student_answer, answer, problem_store): answer 
            for answer in student_answers
        }
        
        # Collect results as they complete
        for future in concurrent.futures.as_completed(future_to_answer):
            try:
                correction = future.result()
                corrections.append(correction)
            except Exception as e:
                answer = future_to_answer[future]
                logger.error(f"Error processing answer {answer.get('q_id')}: {e}")
                # Add a default correction for failed answers
                corrections.append(Correction(
                    q_id=answer.get("q_id", "unknown"),
                    type=answer.get("type", "概念题"),
                    score=0.0,
                    max_score=10.0,
                    confidence=0.0,
                    comment=f"Processing error: {str(e)}",
                    steps=[]
                ))
    
    logger.info(f"Completed processing for student {student_id}")
    return {
        "student_id": student_id,
        "corrections": corrections
    }

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
        
        # Process answers in parallel with increased workers
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            future_to_answer = {
                executor.submit(process_student_answer, answer, problem_store): answer 
                for answer in student_answers
            }
            
            for future in concurrent.futures.as_completed(future_to_answer):
                try:
                    correction = future.result()
                    corrections.append(correction)
                except Exception as e:
                    answer = future_to_answer[future]
                    logger.error(f"Error processing answer {answer.get('q_id')}: {e}")
                    corrections.append(Correction(
                        q_id=answer.get("q_id", "unknown"),
                        type=answer.get("type", "概念题"),
                        score=0.0,
                        max_score=10.0,
                        confidence=0.0,
                        comment=f"Processing error: {str(e)}",
                        steps=[]
                    ))
        
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
    """Run the grading task for all students using parallel processing."""
    logger.info(f"Batch grading task {job_id} started for all students")
    
    try:
        # Log the number of students to be processed
        student_count = len([s for s in student_store if s.get("stu_id")])
        logger.info(f"Found {student_count} students to process")
        
        # Process each student in parallel with increased workers
        all_results = []
        
        # Use ProcessPoolExecutor for CPU-intensive tasks or ThreadPoolExecutor for I/O-intensive tasks
        # Since we're making API calls, ThreadPoolExecutor is more appropriate
        # Increased max_workers for better parallelization
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            # Submit all student processing tasks
            future_to_student = {
                executor.submit(process_student_submission, student, problem_store): student 
                for student in student_store if student.get("stu_id")
            }
            
            # Collect results as they complete
            for future in concurrent.futures.as_completed(future_to_student):
                try:
                    result = future.result()
                    if result:
                        all_results.append(result)
                        logger.info(f"Processed student result: {result.get('student_id', 'unknown')}")
                except Exception as e:
                    student = future_to_student[future]
                    student_id = student.get("stu_id", "unknown")
                    logger.error(f"Error processing student {student_id}: {e}")
        
        # Store the results
        GRADING_RESULTS[job_id] = {
            "status": "completed",
            "results": all_results
        }
        
        logger.info(f"Batch grading task {job_id} completed for all students. Processed {len(all_results)} students.")
        logger.info(f"Stored result for {job_id}: {GRADING_RESULTS[job_id]}")
        
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
    
    # Log the job creation
    logger.info(f"Created new batch grading job: {job_id}")
    logger.info(f"Current jobs: {list(GRADING_RESULTS.keys())}")
    
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
    # Debug logging
    logger.info(f"Checking result for job_id: {job_id}")
    logger.info(f"Available job IDs: {list(GRADING_RESULTS.keys())}")
    
    result = GRADING_RESULTS.get(job_id, {"status": "not_found"})
    logger.info(f"Returning result for {job_id}: {result}")
    return result

@router.get("/all_jobs")
def get_all_jobs():
    """
    Get all job IDs and their statuses for debugging.
    """
    job_statuses = {}
    for job_id, result in GRADING_RESULTS.items():
        job_statuses[job_id] = result.get("status", "unknown")
    return job_statuses