import time
import uuid
import threading
from fastapi import APIRouter
from fastapi.middleware.cors import CORSMiddleware


# # 创建FastAPI应用实例
# app = FastAPI()

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],            # 开发时可以用 "*"；生产请改为你前端的源
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

router = APIRouter(
    prefix="/ai_grading",
    tags=["ai_grading"]
)

# 用一个简单的字典来模拟数据库，存储任务状态
# 在生产环境中，您应该使用Redis, Celery或数据库来代替
JOBS = {}

def run_long_task(job_id: str):
    """一个模拟耗时任务的函数。"""
    print(f"任务 {job_id} 开始运行...")
    time.sleep(15)  # 模拟15秒的处理时间
    JOBS[job_id]["status"] = "completed"
    print(f"任务 {job_id} 已完成。")

@router.post("/")
def start_job():
    """
    接收启动任务的请求。
    立即返回一个任务ID，并在后台线程中开始执行任务。
    """
    job_id = str(uuid.uuid4())
    JOBS[job_id] = {"status": "pending"}
    
    # 使用线程在后台运行耗时任务，这样API可以立即返回
    thread = threading.Thread(target=run_long_task, args=(job_id,))
    thread.start()
    
    return {"job_id": job_id}

@router.get("/{job_id}")
def get_job_status(job_id: str):
    """
    根据任务ID查询并返回任务的当前状态。
    """
    return JOBS.get(job_id, {"status": "not_found"})

# 如何运行此后端:
# 1. 安装所需库: pip install fastapi "uvicorn[standard]"
# 2. 在终端中运行: uvicorn backend_app:app --reload
