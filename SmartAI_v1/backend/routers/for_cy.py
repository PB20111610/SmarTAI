# TODO:一些示例库，没用到的也可以删删
import copy
from typing import List, Dict, Any
import asyncio

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from langchain_core.messages import SystemMessage, HumanMessage

from ..dependencies import *

# --- 日志和应用基础设置 ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# TODO:改成你的文件名
router = APIRouter(
    prefix="/your_file_name",
    tags=["your_file_name"]
)

#TODO: 你设计的system prompt
SYSTEM_PROMPT="""
"""

# TODO: 这是你的核心AI处理函数，不要用异步函数，就普通函数
def ai_process(
    other_parameters: Any, #TODO: 放其他参数，参数类型可改，在 from typing中课添加你需要的数据类型
    llm: Any, # 接收LLM客户端实例
    problems_data: Dict[str, Dict[str,str]],
    student_data: List[Dict[str, Any]],
) -> Dict[str, Any]:
    
    # 我们数据格式对接转换过程如下，TODO:如果你的后端分了多个文件还都需要用可能还是要 dependencies.py存一下全局变量
    ans_stu_dict = copy.deepcopy(problems_data)
    for q_id in ans_stu_dict.keys():
        ans_stu_dict[q_id]["content"] = []

    for stu in student_data:
        stu_id = stu["stu_id"]
        stu_name = stu["stu_name"]
        for ans in stu["stu_ans"]:
            stu_ans = {}
            stu_ans["stu_id"] = stu_id
            stu_ans["stu_name"] = stu_name
            stu_ans["answers"] = ans["content"]
            ans_q_id = ans["q_id"]
            ans_stu_dict[ans_q_id]["content"].append(stu_ans)

    messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content="你需要上传给ai的内容，可以全部仿照我 hw_preview.py")
        ]
    raw_llm_output = llm.invoke(messages).content
    json_output = parse_llm_json_output(raw_llm_output, StudentSubmission)
        # 将返回的 Pydantic 对象转换为字典并添加到结果列表
    logger.info(f"提取到学生解答:{json_output.model_dump()}")
    
    return "TODO:"
    
#TODO:问问ai这里还是不是post
@router.post("/")
async def your_function_name(
    problem_store: Dict = Depends(get_problem_store),
    student_store: List = Depends(get_student_store),
    llm: Any = Depends(get_llm),
    your_other_parameters: Any,
    ):
    logger.info(f"......")
    
    try:        
        # 2. 调用核心AI处理函数
        # 将解码后的文本和注入的依赖传递给服务函数
        # recognized_hw = await process_and_store_problems(
        #     text=text,
        #     llm=llm,
        #     problem_store=problem_store
        # )
        
        graded_hw = await asyncio.to_thread(
            ai_process,
            other_parameters=your_other_parameters,
            llm=llm,
            problem_data=problem_store,
            student_data=student_store
        )
        logger.info("xxxxxx")

        
        # 3. 返回成功响应TODO:这里是不是这样写JSONResponse也问问AI，感觉应该是的
        return JSONResponse(content=graded_hw)

    except HTTPException as e:
        # 直接抛出由服务函数或解码函数生成的HTTPException
        raise e
    except Exception as e:
        logger.exception(f"发生未知错误。")
        raise HTTPException(status_code=500, detail=f"服务器内部错误: {e}")