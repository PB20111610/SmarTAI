# dependencies.py
import os
import logging
from typing import Dict, List, Any, Type
from pydantic import BaseModel, Field, ValidationError
from langchain_openai import ChatOpenAI

# # 这是一个我们希望在不同路由间共享的 Python 变量
# # 它可以是任何东西：一个数据库连接池、一个配置对象、一个AI模型实例等
# fake_db: Dict[str, Any] = {"items": {}, "users": {}}

# # 这是“依赖函数”（或称为 "dependency"）
# # FastAPI 会在处理请求时调用这个函数，并将其返回值注入到需要它的地方
# def get_db() -> Dict[str, Any]:
#     """返回共享的数据库实例"""
#     return fake_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 您需要使用支持视觉（多模态）的模型，例如 "gpt-4o"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "8dcdf3e9238f48f4ae329f638e66dfe2.HHIbfrj5M4GcjM8f")
OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://open.bigmodel.cn/api/paas/v4")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "glm-4")

CONTEXT_WINDOW_THRESHOLD_CHARS = 200000 

if not OPENAI_API_KEY:
    logger.error("环境变量 OPENAI_API_KEY 未设置，后端调用将失败！")

try:
    client = ChatOpenAI(
        api_key=OPENAI_API_KEY,
        base_url=OPENAI_API_BASE,
    )
except Exception as e:
    logger.error(f"初始化OpenAI客户端失败: {e}")
    client = None

# NOTE:zhipu ai直接复制这部分代码
zhipu_ai = ChatOpenAI(
            model=OPENAI_MODEL,
            temperature=0.0,
            api_key=OPENAI_API_KEY,
            base_url=OPENAI_API_BASE,
        )


# ... (ProblemInfo 和 ProblemSet 的定义保持不变) ...
class ProblemInfo(BaseModel):
    q_id: str = Field(description="题目唯一标识，\"q1\" 开始依次递增为 \"q2\"、\"q3\"...")
    number: str = Field(description="题目包含的题号，如\"1\"、\"2.3\"、\"第二题\", \"III.\" 等，若不存在，则取题目\"q_id\"的阿拉伯数字作为题号\"number\"")
    type: str = Field(description="题目类型，包括:概念题、计算题、编程题、证明题、推理题；如果无法归为以上5类，则为其他。")
    stem: str = Field(description="题目**完整**的题干内容，包括所有文字、公式和代码块。**[重要指令]：请保证提取题干的完整性，你被禁止自行删减内容，也不允许进行翻译，请“完整”保留题干信息，你的工作只是将他们划分为多个题目。**")
    criterion: str = Field(description="题目评分标准细则")

class ProblemSet(BaseModel):
    """A collection of problems extracted from a document."""
    problems: List[ProblemInfo] = Field(description="将所有处理好的题目整合成一个字典，key为\"problems\"，value为一个列表，列表每个元素是一个JSON对象字典，包含 \"q_id\", \"number\", \"type\", \"stem\", \"criterion\" 这几个字段。")


# 单个题目答案的结构
class StudentAnswerInfo(BaseModel):
    q_id: str = Field(description="题目唯一标识，必须与输入题目数据中的 q_id 完全一致。")
    number: str = Field(description="题号，必须与输入题目数据中的 number 完全一致。")
    type: str = Field(description="题目类型，必须与输入题目数据中的 type 完全一致。")
    content: str = Field(description="从学生作答文本中提取出的对应这道题的完整答案内容。如果学生未作答，请将此字段设为空字符串")
    flag: List[str] = Field(description="该题目分割识别时遇到的任何处理置信度不高或者完全无法处理的情况，以列表包含所有可能存在的问题。如果没有任何问题，则为空列表")

# 单个学生的完整提交内容结构 (这是我们希望 AI 在单次调用中为每个文件生成的目标结构)
class StudentSubmission(BaseModel):
    stu_id: str = Field(description="从文件名中提取的学生学号，通常是字母和数字的组合或者纯数字；若不存在，则填写空字符串。")
    stu_name: str = Field(description="从文件名中提取的学生姓名，通常是2~4个汉字，或者是包含首字母大写的拼音名或英文名；若不存在，则填写空字符串。")
    stu_ans: List[StudentAnswerInfo] = Field(description="一个包含该生所有题目答案的列表，列表每个元素是一个json字典，包含key:\"q_id\"（题目唯一标识，来自【题目数据】）、\"number\"（题目作答中显示的题号，来自【题目数据】）、\"type\"（题目类型分类，来自【题目数据】）、\"content\"（识别得到的解答过程）、\"flag\"（识别异常情况，见下面详述）")
  
# ... (Student 和 StudentAnswer 的 Pydantic 模型定义，如果需要的话) ...

# --- 独立的内存存储变量 ---

# 用于存储AI生成的题目数据。
# 它的结构将是 {"problems": [...]}, 正好是 ProblemSet dump后的样子。
# 初始化为空字典。
'''
{
    "q1": {"q_id": "q1", "number": "1.1", "type": "概念题", "stem": "请解释什么是“依赖注入”？", "criterion": "满分10分，答错全扣分，答对满分。"},
    "q2": {"q_id": "q2", "number": "1.2", "type": "计算题", "stem": "求解方程 $x^2 - 5x + 6 = 0$。", "criterion": "满分10分，两个结果每个2分，计算过程6分"},
    "q3": {"q_id": "q3", "number": "2", "type": "编程题", "stem": "使用Python编写一个快速排序算法。", "criterion": "满分10分，6个测试样例每通过一个1分，是快速排序算法4分。"},
    "q4": {"q_id": "q4", "number": "3.1", "type": "证明题", "stem": "证明三角形内角之和为180度", "criterion": "每步推导1分，正确证明了结论2分。"},
    "q5": {"q_id": "q5", "number": "3.2", "type": "推理题", "stem": "向上抛出一个小球，测出小球抛出后两次经过某竖直位置$A$的时间间隔$T_A$和经过另一竖直位置$B$的时间间隔$T_B$。若已知$B$在$A$上方$h$处，试求重力加速度$g$", "criterion": "每步推导1分，正确推理出了结论4分。"},
}
'''
problem_data: Dict[str, Dict[str,str]] = {}

# 用于存储学生提交的数据。
# 它的结构将是一个列表 [ {student_dict_1}, {student_dict_2} ]
'''
[
    {
        "stu_id":"stu1",
        "stu_name":"张三",
        "stu_ans":
        [
            {"q_id": "q1", "number": "1.1", "type": "概念题", "content":"ans1", "flag":[]},
            {"q_id": "q2", "number": "1.2", "type": "计算题", "content":"ans2",},
            {"q_id": "q3", "number": "2", "type": "编程题", "content":"ans3",},
            {"q_id": "q4", "number": "3.1", "type": "证明题", "content":"ans4",},
            {"q_id": "q5", "number": "3.2", "type": "推理题", "content":"ans5",},
        ],
    },
    {
        "stu_id":"stu2",
        "stu_name":"李四",
        "stu_ans":
        [
            {"q_id": "q1", "number": "1.1", "type": "概念题", "content":"ans1",},
            {"q_id": "q2", "number": "1.2", "type": "计算题", "content":"ans2",},
            {"q_id": "q3", "number": "2", "type": "编程题", "content":"ans3",},
            {"q_id": "q4", "number": "3.1", "type": "证明题", "content":"ans4",},
            {"q_id": "q5", "number": "3.2", "type": "推理题", "content":"ans5",},
        ],
    },
]
'''
student_data: List[Dict[str, Any]] = []


# --- 独立的依赖函数 ---

def get_problem_store() -> Dict[str, Dict[str,str]]:
    """依赖函数：返回题目数据的存储字典。"""
    return problem_data

def get_student_store() -> List[Dict[str, Any]]:
    """依赖函数：返回学生数据的存储列表。"""
    return student_data

def get_llm() -> ChatOpenAI:
    """返回共享的LLM客户端实例。"""
    if zhipu_ai is None:
        raise RuntimeError("LLM client is not initialized.")
    return zhipu_ai

import re
import json

# def parse_llm_json_output(llm_output: str, output_model: Type[BaseModel]) -> BaseModel:
#     """
#     一个通用的、健壮的函数，用于从LLM的原始文本输出中提取JSON并使用Pydantic模型进行解析。

#     它能处理LLM输出中常见的问题，例如：
#     - JSON对象前后包含解释性文字或提示语。
#     - 使用了Markdown的json代码块标记。
#     - 不规则的换行和空白。

#     Args:
#         llm_output: 从LLM获取的原始字符串响应。
#         output_model: 用于验证和数据转换的Pydantic模型类。

#     Returns:
#         一个已经验证和解析过的Pydantic模型实例。

#     Raises:
#         ValueError: 如果在llm_output中找不到有效的JSON结构，
#                     或者提取的JSON字符串格式错误，
#                     或者JSON内容不符合output_model的定义。
#     """
#     # 优先匹配JSON对象 `{...}`，因为它是最常见的顶层结构
#     match = re.search(r'\{.*\}', llm_output, re.DOTALL)

#     # 如果没有找到JSON对象，再尝试匹配JSON数组 `[...]`
#     if not match:
#         match = re.search(r'\[.*\]', llm_output, re.DOTALL)

#     if not match:
#         raise ValueError(
#             "在LLM输出中未找到有效的JSON对象或数组结构。\n"
#             f"原始输出: '{llm_output}...'" # 只显示部分输出以防过长
#         )

#     json_str = match.group(0)

#     try:
#         # 使用Pydantic V2的 `model_validate_json` 方法，它会一步完成JSON解析和模型验证
#         return output_model.model_validate_json(json_str)
#     except json.JSONDecodeError as e:
#         # 捕获JSON语法错误，例如尾随逗号、引号未闭合等
#         # raise ValueError(
#         #     f"提取的字符串不是一个有效的JSON。错误: {e}\n"
#         #     f"提取的字符串: '{json_str}...'"
#         # )

#         logger.error(f"提取的字符串: {json_str}")
#         with open("error_json.txt", "w", encoding="utf-8") as file:
#             file.write(json_str)
#         raise ValueError(
#             f"JSON内容不符合Pydantic模型定义。错误: {e}"
#         )
#     except ValidationError as e:
#         # 捕获Pydantic验证错误，例如字段缺失、类型不匹配等
#         # raise ValueError(
#         #     f"JSON内容不符合Pydantic模型定义。错误: {e}\n"
#         #     f"提取的字符串: '{json_str}...'"
#         # )
#         logger.error(f"提取的字符串: {json_str}")
#         with open("error_json.txt", "w", encoding="utf-8") as file:
#             file.write(json_str)
#         raise ValueError(
#             f"JSON内容不符合Pydantic模型定义。错误: {e}"
#         )


def parse_llm_json_output(llm_output: str, output_model: Type[BaseModel]) -> BaseModel:
    """
    一个通用的、健壮的函数，用于从LLM的原始文本输出中提取JSON并使用Pydantic模型进行解析。

    [最终版]：能精准修复非法的反斜杠转义错误，同时保留合法的转义符（如 \\n, \\t）。
    """
    match = re.search(r'\{.*\}', llm_output, re.DOTALL)
    if not match:
        match = re.search(r'\[.*\]', llm_output, re.DOTALL)

    if not match:
        raise ValueError(f"在LLM输出中未找到有效的JSON结构。原始输出: '{llm_output[:200]}...'")

    json_str = match.group(0)

    try:
        # 第一次尝试直接解析
        return output_model.model_validate_json(json_str)
    except ValidationError as e:
        # 检查是否是由于JSON语法无效（特别是转义问题）导致的验证错误
        # e.errors() 返回一个错误字典列表，我们检查第一个错误的类型
        first_error = e.errors()[0] if e.errors() else {}
        error_type = first_error.get('type')
        
        # 精准定位到由 'invalid escape' 引起的 'json_invalid' 错误
        if error_type == 'json_invalid' and "invalid escape" in str(e):
            print("检测到Pydantic报告了JSON转义错误，尝试智能修复...")

            # 使用否定前瞻正则表达式，仅将非法的转义反斜杠加倍
            # 这会修复 \a, \b, \c... 但会忽略 \n, \t, \", \\ 等
            json_str_fixed = re.sub(r'\\(?![ntrbf"\\/])', r'\\\\', json_str)
            
            try:
                # 再次尝试解析修复后的字符串
                print("修复成功，再次解析...")
                return output_model.model_validate_json(json_str_fixed)
            except Exception as final_e:
                # 如果修复后仍然失败，则抛出信息更全的错误
                logger.error(f"提取的字符串: {json_str}")
                logger.error(f"修复的字符串: {json_str_fixed}")
                with open("error_json.txt", "w", encoding="utf-8") as file:
                    file.write(json_str)
                with open("error_fixed_json.txt", "w", encoding="utf-8") as file:
                    file.write(json_str_fixed)
                raise ValueError(
                    f"自动修复转义字符后解析仍然失败。\n"
                    f"原始错误: {e}\n"
                    f"最终错误: {final_e}"
                )
        else:
            # 如果是其他类型的JSON错误，直接抛出
            logger.error(f"提取的字符串: {json_str}")
            with open("error_json.txt", "w", encoding="utf-8") as file:
                file.write(json_str)

            raise ValueError(f"提取的字符串不是一个有效的JSON。错误: {e}")
