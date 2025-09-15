import os
import io
import logging
import zipfile
import rarfile
import py7zr
import tarfile
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# --- 日志和应用基础设置 ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# app = FastAPI(
#     title="智能作业核查 AI 后端",
#     description="接收学生作业压缩包，进行AI分析，并返回结构化数据。"
# )

# # 允许所有来源的跨域请求，便于本地开发
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

router = APIRouter(
    prefix="/hw_preview",
    tags=["hw_preview"]
)

# --- 核心 AI 处理逻辑 (模拟) ---

def process_homework_files(archive_files: list, archive_type: str):
    """
    这是核心的AI处理函数（模拟）。
    在真实世界中，您需要在这里集成OCR、文档解析和LLM调用。

    - 遍历 `archive_files` 中的每个文件。
    - 根据文件类型（PDF, JPG, DOCX, PY等）提取内容。
    - 使用AI模型进行题目和答案的分割、识别和分析。
    - 识别学生信息（例如从文件名）。
    - 生成结构化的JSON输出。

    为了演示，我们这里只基于文件名做一个简单的模拟。
    """
    logger.info(f"开始处理一个 {archive_type} 压缩包，包含 {len(archive_files)} 个文件。")
    
    # 模拟从作业中识别出的题目列表
    students_data = {}
    
    for filename in archive_files:
        # 模拟从文件名 "2024001_张三.pdf" 中提取学生ID
        try:
            student_id_name = os.path.splitext(os.path.basename(filename))[0]
            if student_id_name not in students_data:
                students_data[student_id_name] = {"answers": []}
            
            # 模拟为每个学生随机生成一些答案和异常标签
            students_data[student_id_name]["answers"].extend([
                {"question_id": "q1", "content": f"这是 {student_id_name} 对概念题的回答。", "flags": ["识别置信度低"]},
                {"question_id": "q2", "content": "x=2 或 x=3", "flags": []},
                {"question_id": "q3", "content": {"main.py": "def quick_sort(arr):\n    # ... implementation ...\n    return arr"}, "flags": ["格式不匹配"]}
            ])
        except Exception:
            # 忽略无法解析的文件名
            continue

    return {
        "students": students_data,
    }

# --- 文件处理与API端点 ---

def get_archive_filelist(file_bytes: bytes, filename: str) -> list:
    """根据文件扩展名，使用合适的库来获取压缩包内的文件列表"""
    file_in_memory = io.BytesIO(file_bytes)
    
    if filename.endswith('.zip'):
        with zipfile.ZipFile(file_in_memory, 'r') as zf:
            return zf.namelist()
    elif filename.endswith('.rar'):
        # rarfile 依赖于外部的 'unrar' 命令行工具
        try:
            with rarfile.RarFile(file_in_memory, 'r') as rf:
                return rf.namelist()
        except rarfile.UNRARError:
            raise HTTPException(status_code=500, detail="服务器环境缺少 'unrar' 工具，无法处理 RAR 文件。")
    elif filename.endswith('.7z'):
        with py7zr.SevenZipFile(file_in_memory, 'r') as szf:
            return szf.getnames()
    elif filename.endswith(('.tar', '.tar.gz', '.tgz', '.tar.bz2', '.tbz2')):
        with tarfile.open(fileobj=file_in_memory, mode='r:*') as tf:
            return tf.getnames()
    else:
        # 如果不是压缩包，就将文件名本身作为列表返回
        return [filename]


@router.post("/")
async def handle_homework_upload(file: UploadFile = File(...)):
    """
    接收上传的作业文件（可以是压缩包或单个文件），进行处理并返回分析结果。
    """
    logger.info(f"接收到文件: {file.filename}, 类型: {file.content_type}")
    
    try:
        file_bytes = await file.read()
        
        # 1. 获取文件列表（无论是压缩包还是单个文件）
        archive_filelist = get_archive_filelist(file_bytes, file.filename)
        
        # 2. 调用核心处理逻辑
        # 注意：这里我们只传递文件名列表进行模拟。在真实场景中，
        # 你需要将文件内容（字节）也传递给AI处理函数。
        archive_type = os.path.splitext(file.filename)[1]
        processed_data = process_homework_files(archive_filelist, archive_type)

        return JSONResponse(content=processed_data)

    except HTTPException as e:
        # 重新抛出已知的HTTP异常
        raise e
    except Exception as e:
        logger.exception(f"处理文件 '{file.filename}' 时发生未知错误。")
        raise HTTPException(status_code=500, detail=f"服务器内部错误: {e}")
