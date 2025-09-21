import re
import json
from typing import Type, List
from pydantic import BaseModel, ValidationError, Field

# ... (您的Pydantic模型定义，如 StudentSubmission 等) ...
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
  

# def parse_llm_json_output(llm_output: str, output_model: Type[BaseModel]) -> BaseModel:
#     """
#     一个通用的、健壮的函数，用于从LLM的原始文本输出中提取JSON并使用Pydantic模型进行解析。

#     [最终版]：能精准修复非法的反斜杠转义错误，同时保留合法的转义符（如 \\n, \\t）。
#     """
#     match = re.search(r'\{.*\}', llm_output, re.DOTALL)
#     if not match:
#         match = re.search(r'\[.*\]', llm_output, re.DOTALL)

#     if not match:
#         raise ValueError(f"在LLM输出中未找到有效的JSON结构。原始输出: '{llm_output[:200]}...'")

#     json_str = match.group(0)

#     try:
#         # 第一次尝试直接解析
#         return output_model.model_validate_json(json_str)
#     except json.JSONDecodeError as e:
#         # 如果是 "invalid escape" 错误，则尝试智能修复
#         if "invalid escape" in str(e):
#             print("检测到JSON转义错误，尝试智能修复...")

#             # 使用否定前瞻正则表达式，仅将非法的转义反斜杠加倍
#             # 这会修复 \a, \b, \c... 但会忽略 \n, \t, \", \\ 等
#             json_str_fixed = re.sub(r'\\(?![ntrbf"\\/])', r'\\\\', json_str)
            
#             try:
#                 # 再次尝试解析修复后的字符串
#                 print("修复成功，再次解析...")
#                 return output_model.model_validate_json(json_str_fixed)
#             except Exception as final_e:
#                 # 如果修复后仍然失败，则抛出信息更全的错误
#                 raise ValueError(
#                     f"自动修复转义字符后解析仍然失败。\n"
#                     f"原始错误: {e}\n"
#                     f"最终错误: {final_e}"
#                 )
#         else:
#             # 如果是其他类型的JSON错误，直接抛出
#             raise ValueError(f"提取的字符串不是一个有效的JSON。错误: {e}")
#     except ValidationError as e:
#         raise ValueError(f"JSON内容不符合Pydantic模型定义。错误: {e}")

def parse_llm_json_output(llm_output: str, output_model: Type[BaseModel]) -> BaseModel:
    """
    一个通用的、健壮的函数，用于从LLM的原始文本输出中提取JSON并使用Pydantic模型进行解析。

    [最终修正版]：正确处理Pydantic V2的错误包装机制，确保在发生'invalid escape'
    错误时能触发并执行智能修复逻辑。
    """
    match = re.search(r'\{.*\}', llm_output, re.DOTALL)
    if not match:
        match = re.search(r'\[.*\]', llm_output, re.DOTALL)

    if not match:
        raise ValueError(f"在LLM输出中未找到有效的JSON结构。原始输出: '{llm_output[:200]}...'")

    json_str = match.group(0)

    try:
        # 正常情况下，一次解析成功
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
            json_str_fixed = re.sub(r'\\(?![ntrbf"\\/])', r'\\\\', json_str)
            
            # 在修复后再次尝试解析
            try:
                print("修复成功，再次解析...")
                return output_model.model_validate_json(json_str_fixed)
            except Exception as final_e:
                # 如果修复后仍然失败，抛出包含完整上下文的错误
                raise ValueError(
                    f"自动修复转义字符后解析仍然失败。\n"
                    f"原始错误: {e}\n"
                    f"最终错误: {final_e}"
                )
        else:
            # 如果是其他类型的验证错误（如字段缺失、类型不匹配等），则直接抛出
            raise ValueError(f"JSON内容不符合Pydantic模型定义，且非可自动修复的转义错误: {e}")


# ==============================================================================
# 使用示例来验证新函数的行为
# ==============================================================================

if __name__ == '__main__':
    # 构造一个同时包含非法LaTex转义和合法\n转义的脏数据
    dirty_llm_output_mixed = r'''
    Here is the data you requested:
    ```json
    {
    "stu_id": "PB20111611",
    "stu_name": "王五",
    "stu_ans": [
            {"q_id": "q1", "number": "1", "type": "概念题", "content": "C", "flag": []},
            {"q_id": "q2", "number": "2", "type": "计算题", "content": "", "flag": ["未作答"]},
            {"q_id": "q3", "number": "3", "type": "证明题", "content": "Let $G$ be a soluble group with a chain of subgroups: ... Thus, $H$ is soluble with a chain of normal subgroups: ... Quotient case: ...", "flag": []},
            {"q_id": "q4", "number": "4", "type": "计算题", "content": "以轴线为轴、 $r$ 为半径，在硫酸铜溶液中取一个厚为 $\mathrm{d}r$，长为 $l$ 的圆筒，这圆筒的电阻为 ... 积分便得 ... 设两筒的电势差为U，内筒上的电荷量为Q，则由对称性和高斯定理得硫酸铜溶液中的电场强度为 ... 所以电容 $C= ...$", "flag": []},
            {"q_id": "q5", "number": "5", "type": "概念题", "content": "人工智能是研究、开发用于模拟、延伸和扩展人的智能的理论、方法、技术及应用系统的一门新的技术科学。", "flag": []},
            {"q_id": "q6", "number": "6", "type": "计算题", "content": "使用因式分解法：$x^2 - 5x + 6 = (x-2)(x-3) = 0$，所以 $x = 2$ 或 $x = 3$。", "flag": []},
            {"q_id": "q7", "number": "7", "type": "证明题", "content": "通过数学归纳法证明：当 $n=1$ 时，$1^2+1=2$ 为偶数。假设当 $n=k$ 时成立，即 $k^2+k$ 为偶数。则当 $n=k+1$ 时，$(k+1)^2+(k+1) = k^2+2k+1+k+1 = (k^2+k)+2(k+1)$。由归纳假设$k^2+k$ 为偶数，$2(k+1)$ 也为偶数，所以和为偶数。证毕。", "flag": []}
        ]
    }
    ```
    '''

    print("--- 测试包含混合转义符的LLM输出 ---")
    try:
        # 为了演示，我们先伪造一个简单的模型

        submission = parse_llm_json_output(dirty_llm_output_mixed, StudentSubmission)
        
        print("\n✅ 解析成功!")
        
        # 验证 \n 是否被保留为真正的换行符
        content_with_newline = submission.stu_ans[0].content
        print(f"\n验证换行符: content字段包含换行符 -> {'\n' in content_with_newline}")
        print("解析后的内容1:")
        print(content_with_newline)
        
        # 验证 \alpha 是否被正确转义并保留
        content_with_latex = submission.stu_ans[1].content
        print(f"\n验证LaTex: content字段包含'\\alpha' -> {'\\alpha' in content_with_latex}")
        print("解析后的内容2:")
        print(content_with_latex)

    except ValueError as e:
        print(f"❌ 解析失败: {e}")