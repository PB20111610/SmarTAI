"""
数据模型和数据加载器模块

包含学生成绩、作业统计、题目分析等数据类以及模拟数据生成器
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
import pandas as pd
import numpy as np
from faker import Faker
import random
import json

fake = Faker('zh_CN')

@dataclass
class StudentScore:
    """学生成绩数据类"""
    student_id: str
    student_name: str
    total_score: float
    max_score: float
    submit_time: datetime
    questions: List[Dict[str, Any]] = field(default_factory=list)
    need_review: bool = False
    confidence_score: float = 0.85
    
    @property
    def percentage(self) -> float:
        """计算百分比得分"""
        return (self.total_score / self.max_score) * 100 if self.max_score > 0 else 0
    
    @property
    def grade_level(self) -> str:
        """获取成绩等级"""
        percentage = self.percentage
        if percentage >= 90:
            return "优秀"
        elif percentage >= 80:
            return "良好"
        elif percentage >= 70:
            return "中等"
        elif percentage >= 60:
            return "及格"
        else:
            return "不及格"

@dataclass
class QuestionAnalysis:
    """题目分析数据类"""
    question_id: str
    question_type: str  # concept, calculation, proof, programming
    topic: str
    difficulty: float  # 0-1
    correct_rate: float
    avg_score: float
    max_score: float
    common_errors: List[str] = field(default_factory=list)
    knowledge_points: List[str] = field(default_factory=list)
    
    @property
    def difficulty_level(self) -> str:
        """获取难度等级"""
        if self.difficulty <= 0.3:
            return "简单"
        elif self.difficulty <= 0.6:
            return "中等"
        else:
            return "困难"

@dataclass
class AssignmentStats:
    """作业统计数据类"""
    assignment_id: str
    assignment_name: str
    total_students: int
    submitted_count: int
    avg_score: float
    max_score: float
    min_score: float
    std_score: float
    pass_rate: float
    question_count: int
    create_time: datetime
    
    @property
    def submission_rate(self) -> float:
        """计算提交率"""
        return (self.submitted_count / self.total_students) * 100 if self.total_students > 0 else 0


class DataLoader:
    """数据加载器类 - 生成模拟数据用于开发测试"""
    
    def __init__(self, seed: int = 42):
        """初始化数据加载器"""
        random.seed(seed)
        np.random.seed(seed)
        Faker.seed(seed)
        
        # 预定义的知识点和题目类型
        self.knowledge_points = [
            "线性代数", "微积分", "概率统计", "数据结构", "算法设计",
            "面向对象编程", "数据库原理", "计算机网络", "操作系统", "软件工程"
        ]
        
        self.question_types = ["concept", "calculation", "proof", "programming"]
        
        self.common_errors = [
            "计算错误", "概念理解不准确", "逻辑推理错误", "语法错误",
            "边界条件处理不当", "算法效率低下", "内存泄漏", "格式错误"
        ]
        
        # 添加样例题目和答案模板
        self.sample_questions = {
            "concept": [
                {
                    "content": "请解释什么是数据结构中的“栈”，并说明其主要特点。",
                    "standard_answer": "栈是一种线性数据结构，遵循后进先出（LIFO）的原则。主要特点：1) 只能在一端进行插入和删除操作；2) 具有push和pop两个基本操作；3) 时间复杂度为O(1)。",
                    "points": ["正确定义栈", "说明LIFO原则", "列出主要操作", "分析时间复杂度"]
                },
                {
                    "content": "请说明面向对象编程中的“封装”概念及其作用。",
                    "standard_answer": "封装是面向对象编程的基本特性之一，指将数据和操作数据的方法组合在一起，对外隐藏内部实现细节。作用：1) 提高代码安全性；2) 降低耦合度；3) 便于维护和修改。",
                    "points": ["定义封装概念", "说明数据隐藏", "列举主要作用"]
                }
            ],
            "calculation": [
                {
                    "content": "计算以下递归函数的时间复杂度：\nint fibonacci(int n) {\n    if (n <= 1) return n;\n    return fibonacci(n-1) + fibonacci(n-2);\n}",
                    "standard_answer": "设 T(n) 为计算 fibonacci(n) 的时间复杂度。\n递推关系：T(n) = T(n-1) + T(n-2) + O(1)\n解得：T(n) = O(2^n)\n因为每个调用都会产生两个子问题，形成二叉树结构。",
                    "points": ["建立递推关系", "正确求解", "给出最终结果", "解释原理"]
                },
                {
                    "content": "已知一个排序数组 arr = [1, 3, 5, 7, 9, 11, 13]，使用二分查找算法查找元素 7，请写出查找过程。",
                    "standard_answer": "二分查找过程：\n1. 初始: left=0, right=6, mid=3, arr[3]=7 ✓\n2. 找到目标元素，返回下标 3\n时间复杂度: O(log n)",
                    "points": ["初始化变量", "正确计算mid", "判断条件", "给出结果"]
                }
            ],
            "proof": [
                {
                    "content": "请证明：对于任意 n 个节点的二叉树，叶子节点的数量等于度为2的节点数量加 1。",
                    "standard_answer": "证明：\n设叶子节点数为 n0，度为1的节点数为 n1，度为2的节点数为 n2。\n总节点数： n = n0 + n1 + n2\n总边数： e = n - 1 = n1 + 2*n2\n由于 n = n0 + n1 + n2，所以 n0 + n1 + n2 - 1 = n1 + 2*n2\n化简得： n0 = n2 + 1",
                    "points": ["定义变量", "建立等式", "正确推导", "得出结论"]
                }
            ],
            "programming": [
                {
                    "content": "请编写一个函数，实现链表的反转操作。\n函数签名：ListNode* reverseList(ListNode* head)",
                    "standard_answer": "```cpp\nListNode* reverseList(ListNode* head) {\n    ListNode* prev = nullptr;\n    ListNode* curr = head;\n    \n    while (curr != nullptr) {\n        ListNode* next = curr->next;\n        curr->next = prev;\n        prev = curr;\n        curr = next;\n    }\n    \n    return prev;\n}\n```",
                    "points": ["初始化指针", "循环判断条件", "正确更新指针", "返回结果"]
                }
            ]
        }
    
    def generate_student_scores(self, count: int = 50) -> List[StudentScore]:
        """生成学生成绩数据"""
        scores = []
        
        for i in range(count):
            # 生成学生基本信息
            student_id = f"2024{str(i+1).zfill(4)}"
            student_name = fake.name()
            
            # 生成作业题目
            question_count = random.randint(8, 15)
            questions = []
            total_score = 0
            max_total = 0
            
            for j in range(question_count):
                max_score = random.choice([5, 10, 15, 20])
                score = max_score * random.uniform(0.3, 1.0)
                
                # 低置信度概率
                confidence = random.uniform(0.6, 0.95)
                
                # 生成详细的评分细则和判分依据
                question_type = random.choice(self.question_types)
                grading_rules = self._generate_grading_rules()
                step_analysis = self._generate_step_analysis(score, max_score, question_type)
                model_output = self._generate_model_output(confidence)
                
                # 生成题目内容和学生答案
                question_content, student_answer, scoring_points = self._generate_question_and_answer(question_type, score, max_score)
                
                question = {
                    "question_id": f"Q{j+1}",
                    "question_type": question_type,
                    "question_title": f"题目{j+1}: {random.choice(['数据结构设计', '算法实现', '程序分析', '概念理解'])}问题",
                    "question_content": question_content["content"],
                    "standard_answer": question_content["standard_answer"],
                    "student_answer": student_answer,
                    "scoring_points": scoring_points,
                    "score": round(score, 1),
                    "max_score": max_score,
                    "confidence": confidence,
                    "feedback": self._generate_feedback(score, max_score),
                    "errors": random.sample(self.common_errors, random.randint(0, 2)) if score < max_score * 0.8 else [],
                    "knowledge_points": random.sample(self.knowledge_points, random.randint(1, 3)),
                    "grading_rules": grading_rules,
                    "step_analysis": step_analysis,
                    "model_output": model_output,
                    "review_notes": self._generate_review_notes(confidence, score, max_score)
                }
                questions.append(question)
                total_score += score
                max_total += max_score
            
            # 生成提交时间
            submit_time = fake.date_time_between(
                start_date='-7d',
                end_date='now'
            )
            
            # 计算是否需要复核
            avg_confidence = np.mean([q["confidence"] for q in questions])
            need_review = avg_confidence < 0.75 or total_score / max_total < 0.6
            
            score_obj = StudentScore(
                student_id=student_id,
                student_name=student_name,
                total_score=round(total_score, 1),
                max_score=max_total,
                submit_time=submit_time,
                questions=questions,
                need_review=need_review,
                confidence_score=avg_confidence
            )
            scores.append(score_obj)
        
        return sorted(scores, key=lambda x: x.total_score, reverse=True)
    
    def generate_question_analysis(self, count: int = 12) -> List[QuestionAnalysis]:
        """生成题目分析数据"""
        analyses = []
        
        for i in range(count):
            question_type = random.choice(self.question_types)
            topic = random.choice(self.knowledge_points)
            difficulty = random.uniform(0.2, 0.9)
            
            # 根据难度计算正确率
            base_correct_rate = 1 - difficulty
            correct_rate = base_correct_rate + random.uniform(-0.2, 0.2)
            correct_rate = max(0.1, min(0.95, correct_rate))
            
            max_score = random.choice([10, 15, 20, 25])
            avg_score = max_score * correct_rate * random.uniform(0.8, 1.2)
            avg_score = max(0, min(max_score, avg_score))
            
            analysis = QuestionAnalysis(
                question_id=f"Q{i+1}",
                question_type=question_type,
                topic=topic,
                difficulty=difficulty,
                correct_rate=correct_rate,
                avg_score=round(avg_score, 1),
                max_score=max_score,
                common_errors=random.sample(self.common_errors, random.randint(1, 4)),
                knowledge_points=random.sample(self.knowledge_points, random.randint(1, 3))
            )
            analyses.append(analysis)
        
        return analyses
    
    def generate_assignment_stats(self) -> AssignmentStats:
        """生成作业统计数据"""
        total_students = random.randint(45, 60)
        submitted_count = random.randint(int(total_students * 0.8), total_students)
        
        # 生成分数统计
        scores = np.random.normal(75, 15, submitted_count)
        scores = np.clip(scores, 0, 100)
        
        avg_score = np.mean(scores)
        max_score = np.max(scores)
        min_score = np.min(scores)
        std_score = np.std(scores)
        pass_rate = np.sum(scores >= 60) / len(scores)
        
        return AssignmentStats(
            assignment_id="ASSIGN_001",
            assignment_name="数据结构与算法 - 期中作业",
            total_students=total_students,
            submitted_count=submitted_count,
            avg_score=round(avg_score, 1),
            max_score=round(max_score, 1),
            min_score=round(min_score, 1),
            std_score=round(std_score, 1),
            pass_rate=round(pass_rate * 100, 1),
            question_count=12,
            create_time=fake.date_time_between(start_date='-30d', end_date='-7d')
        )
    
    def _generate_feedback(self, score: float, max_score: float) -> str:
        """生成评语反馈"""
        percentage = (score / max_score) * 100
        
        if percentage >= 90:
            return random.choice([
                "回答完全正确，思路清晰，表达准确！",
                "解题方法正确，步骤清楚，值得表扬！",
                "完美的答案，展现了扎实的基础知识！"
            ])
        elif percentage >= 80:
            return random.choice([
                "回答基本正确，但在细节处理上还可以更仔细。",
                "思路正确，但表达可以更加准确。",
                "良好的解答，建议在计算精度上多加注意。"
            ])
        elif percentage >= 60:
            return random.choice([
                "基本理解了题意，但在具体实现上存在问题。",
                "思路有一定正确性，但需要加强基础知识的掌握。",
                "部分正确，建议复习相关概念。"
            ])
        else:
            return random.choice([
                "解答存在较大问题，建议重新学习相关知识点。",
                "理解有偏差，需要加强基础概念的学习。",
                "答案不够准确，建议寻求老师或同学的帮助。"
            ])
    
    def _generate_grading_rules(self) -> Dict[str, Any]:
        """生成评分细则和判分依据"""
        return {
            "scoring_criteria": [
                {
                    "criterion": "算法思路正确性",
                    "weight": 0.4,
                    "points": random.uniform(0.6, 1.0),
                    "description": "考查学生对算法核心思想的理解"
                },
                {
                    "criterion": "代码实现质量",
                    "weight": 0.3,
                    "points": random.uniform(0.5, 0.9),
                    "description": "代码的可读性、规范性和效率"
                },
                {
                    "criterion": "边界情况处理",
                    "weight": 0.2,
                    "points": random.uniform(0.3, 0.8),
                    "description": "对异常情况和边界条件的处理"
                },
                {
                    "criterion": "注释和文档",
                    "weight": 0.1,
                    "points": random.uniform(0.4, 0.9),
                    "description": "代码注释的完整性和清晰度"
                }
            ],
            "auto_rules_hit": [
                f"规则R{random.randint(1,10)}: 语法正确性检查",
                f"规则R{random.randint(11,20)}: 逻辑结构合理性",
                f"规则R{random.randint(21,30)}: 变量命名规范性"
            ][:random.randint(1, 3)]
        }
    
    def _generate_step_analysis(self, score: float, max_score: float, question_type: str = "programming") -> List[Dict[str, Any]]:
        """生成基于题型的逐步分析结果"""
        # 根据题型定义不同的评分步骤
        step_templates = {
            "concept": [
                {"title": "概念理解准确性", "weight": 0.4, "threshold": 0.8},
                {"title": "定义表述完整性", "weight": 0.3, "threshold": 0.7},
                {"title": "举例与应用", "weight": 0.2, "threshold": 0.6},
                {"title": "表达清晰度", "weight": 0.1, "threshold": 0.5}
            ],
            "calculation": [
                {"title": "公式选择与建立", "weight": 0.3, "threshold": 0.8},
                {"title": "计算步骤正确性", "weight": 0.4, "threshold": 0.7},
                {"title": "最终结果准确性", "weight": 0.2, "threshold": 0.6},
                {"title": "过程规范性", "weight": 0.1, "threshold": 0.5}
            ],
            "proof": [
                {"title": "前提条件识别", "weight": 0.25, "threshold": 0.8},
                {"title": "逻辑推理过程", "weight": 0.4, "threshold": 0.7},
                {"title": "步骤完整性", "weight": 0.25, "threshold": 0.6},
                {"title": "结论表述", "weight": 0.1, "threshold": 0.5}
            ],
            "programming": [
                {"title": "问题理解与分析", "weight": 0.2, "threshold": 0.8},
                {"title": "算法设计与选择", "weight": 0.3, "threshold": 0.7},
                {"title": "代码实现", "weight": 0.4, "threshold": 0.6},
                {"title": "测试与验证", "weight": 0.1, "threshold": 0.5}
            ]
        }
        
        # 获取对应题型的步骤模板
        templates = step_templates.get(question_type, step_templates["programming"])
        
        steps = []
        score_ratio = score / max_score if max_score > 0 else 0
        
        for i, template in enumerate(templates):
            step_score_ratio = min(1.0, max(0.0, score_ratio + random.uniform(-0.2, 0.2)))
            is_correct = step_score_ratio >= template["threshold"]
            
            points_earned = max_score * template["weight"] * step_score_ratio
            max_points = max_score * template["weight"]
            
            # 生成基于题型和步骤的反馈
            feedback = self._generate_step_feedback(question_type, template["title"], is_correct, step_score_ratio)
            error_type = self._get_error_type(question_type, template["title"]) if not is_correct else None
            
            step = {
                "step_number": i + 1,
                "step_title": template["title"],
                "is_correct": is_correct,
                "points_earned": round(points_earned, 1),
                "max_points": round(max_points, 1),
                "feedback": feedback,
                "error_type": error_type,
                "highlight": not is_correct
            }
            steps.append(step)
        
        return steps
    
    def _generate_step_feedback(self, question_type: str, step_title: str, is_correct: bool, score_ratio: float) -> str:
        """生成基于题型和步骤的具体反馈"""
        feedback_templates = {
            "concept": {
                "概念理解准确性": {
                    True: ["概念理解准确，定义清晰", "对核心概念把握到位", "概念掌握扎实"],
                    False: ["概念理解有偏差", "核心定义不准确", "概念混淆"]
                },
                "定义表述完整性": {
                    True: ["定义表述完整，要点齐全", "表述全面，逻辑清晰"],
                    False: ["定义不够完整，缺少关键要点", "表述过于简略"]
                },
                "举例与应用": {
                    True: ["举例恰当，应用合理", "能够结合实际应用"],
                    False: ["缺少具体举例", "应用场景理解不足"]
                },
                "表达清晰度": {
                    True: ["表达清晰，逻辑明确", "语言准确，条理清楚"],
                    False: ["表达不够清晰", "逻辑不够清楚"]
                }
            },
            "calculation": {
                "公式选择与建立": {
                    True: ["公式选择正确，建立合理", "数学模型准确"],
                    False: ["公式选择错误", "数学建模有问题"]
                },
                "计算步骤正确性": {
                    True: ["计算步骤正确，过程清晰", "运算准确无误"],
                    False: ["计算过程有错误", "运算步骤不正确"]
                },
                "最终结果准确性": {
                    True: ["最终结果正确", "答案准确"],
                    False: ["最终结果错误", "答案不准确"]
                },
                "过程规范性": {
                    True: ["解题过程规范，格式正确", "步骤完整规范"],
                    False: ["过程不够规范", "格式需要改进"]
                }
            },
            "proof": {
                "前提条件识别": {
                    True: ["前提条件识别准确", "已知条件理解正确"],
                    False: ["前提条件理解有误", "已知条件识别不准确"]
                },
                "逻辑推理过程": {
                    True: ["逻辑推理严密，步骤清晰", "推理过程合理"],
                    False: ["逻辑推理有漏洞", "推理步骤不严密"]
                },
                "步骤完整性": {
                    True: ["证明步骤完整", "推导过程完整"],
                    False: ["证明步骤不完整", "缺少关键推导步骤"]
                },
                "结论表述": {
                    True: ["结论表述清晰准确", "最终结论正确"],
                    False: ["结论表述不清楚", "结论不准确"]
                }
            },
            "programming": {
                "问题理解与分析": {
                    True: ["正确理解了问题要求，分析清晰", "问题分析到位"],
                    False: ["问题理解有偏差", "需求分析不准确"]
                },
                "算法设计与选择": {
                    True: ["算法选择合理", "算法设计正确"],
                    False: ["算法选择不够优化", "算法设计有问题"]
                },
                "代码实现": {
                    True: ["实现正确", "代码质量良好"],
                    False: ["实现有较大问题", "代码存在错误"]
                },
                "测试与验证": {
                    True: ["测试充分", "验证完整"],
                    False: ["缺少必要测试", "验证不充分"]
                }
            }
        }
        
        templates = feedback_templates.get(question_type, feedback_templates["programming"])
        step_templates = templates.get(step_title, {True: ["表现良好"], False: ["需要改进"]})
        feedback_list = step_templates.get(is_correct, ["评价中"])
        
        return random.choice(feedback_list)
    
    def _get_error_type(self, question_type: str, step_title: str) -> str:
        """根据题型和步骤获取错误类型"""
        error_types = {
            "concept": {
                "概念理解准确性": "概念理解错误",
                "定义表述完整性": "定义不完整",
                "举例与应用": "应用理解不足",
                "表达清晰度": "表达不清"
            },
            "calculation": {
                "公式选择与建立": "公式错误",
                "计算步骤正确性": "计算错误",
                "最终结果准确性": "结果错误",
                "过程规范性": "格式问题"
            },
            "proof": {
                "前提条件识别": "前提理解错误",
                "逻辑推理过程": "逻辑错误",
                "步骤完整性": "步骤不完整",
                "结论表述": "结论错误"
            },
            "programming": {
                "问题理解与分析": "需求理解错误",
                "算法设计与选择": "算法效率问题",
                "代码实现": "逻辑错误",
                "测试与验证": "测试不充分"
            }
        }
        
        types = error_types.get(question_type, error_types["programming"])
        return types.get(step_title, "其他错误")
    
    def _generate_model_output(self, confidence: float) -> Dict[str, Any]:
        """生成模型输出和运行日志"""
        return {
            "model_name": random.choice(["GPT-4-Turbo", "Claude-3-Opus", "Gemini-Pro", "Custom-Grader-v2.1"]),
            "processing_time": f"{random.uniform(0.5, 3.2):.2f}s",
            "confidence_score": confidence,
            "reasoning_tokens": random.randint(150, 800),
            "output_summary": "模型识别出代码结构清晰，但在算法优化方面存在改进空间" if confidence < 0.8 else "模型识别出优秀的解决方案，符合最佳实践",
            "log_entries": [
                f"[INFO] 开始分析代码结构... (timestamp: {random.randint(1000, 9999)}ms)",
                f"[DEBUG] 检测到函数定义: {random.randint(3, 8)}个",
                f"[INFO] 语法分析完成，编译通过",
                f"[WARN] 发现潜在性能问题: 循环复杂度" if confidence < 0.75 else f"[INFO] 性能分析通过",
                f"[INFO] 置信度评估完成: {confidence:.2%}"
            ]
        }
    
    def _generate_review_notes(self, confidence: float, score: float, max_score: float) -> Dict[str, Any]:
        """生成复核建议和注意事项"""
        needs_review = confidence < 0.75 or (score / max_score) < 0.6
        
        return {
            "needs_review": needs_review,
            "review_priority": "High" if confidence < 0.6 else "Medium" if confidence < 0.75 else "Low",
            "review_reasons": [
                "置信度低于阈值" if confidence < 0.75 else None,
                "得分低于标准" if (score / max_score) < 0.6 else None,
                "模型输出不一致" if confidence < 0.65 else None
            ],
            "suggested_actions": [
                "人工复核代码逻辑" if needs_review else None,
                "检查评分标准一致性" if confidence < 0.7 else None,
                "与学生沟通确认" if (score / max_score) < 0.5 else None
            ],
            "estimated_review_time": f"{random.randint(5, 20)}分钟" if needs_review else "0分钟"
        }
    
    def _generate_question_and_answer(self, question_type: str, score: float, max_score: float) -> tuple:
        """生成题目内容和学生答案"""
        # 从样例题目中随机选择
        question_template = random.choice(self.sample_questions[question_type])
        
        # 生成学生答案（根据得分情况生成不同质量的答案）
        percentage = (score / max_score) * 100
        student_answer = self._generate_student_answer(question_type, question_template, percentage)
        
        # 生成评分点分析
        scoring_points = self._generate_scoring_points_analysis(question_template["points"], percentage)
        
        return question_template, student_answer, scoring_points
    
    def _generate_student_answer(self, question_type: str, question_template: dict, percentage: float) -> str:
        """根据得分情况生成学生答案"""
        if percentage >= 90:  # 优秀答案
            return self._generate_excellent_answer(question_type, question_template)
        elif percentage >= 75:  # 良好答案
            return self._generate_good_answer(question_type, question_template)
        elif percentage >= 60:  # 中等答案
            return self._generate_average_answer(question_type, question_template)
        else:  # 较差答案
            return self._generate_poor_answer(question_type, question_template)
    
    def _generate_excellent_answer(self, question_type: str, template: dict) -> str:
        """生成优秀答案"""
        if question_type == "concept":
            return template["standard_answer"] + "附加说明：还可以结合实际应用场景来理解。"
        elif question_type == "calculation":
            return template["standard_answer"] + "\n\n验证：可以通过代入具体数值进行检验。"
        elif question_type == "proof":
            return template["standard_answer"] + "\n\n注：这个结论在树结构分析中非常重要。"
        else:  # programming
            return template["standard_answer"] + "\n\n// 时间复杂度: O(n), 空间复杂度: O(1)"
    
    def _generate_good_answer(self, question_type: str, template: dict) -> str:
        """生成良好答案（有小缺陷）"""
        if question_type == "concept":
            # 缺少一些细节
            answer = template["standard_answer"]
            return answer.replace("时间复杂度为O(1)", "操作很快")
        elif question_type == "calculation":
            # 答案正确但缺少解释
            lines = template["standard_answer"].split('\n')
            return '\n'.join(lines[:-1])  # 去掉最后一行解释
        elif question_type == "proof":
            # 证明步骤正确但略显粗糙
            return template["standard_answer"].replace("化简得：", "所以：")
        else:  # programming
            # 代码正确但缺少注释
            return template["standard_answer"].replace("    ", "  ")  # 缩进不规范
    
    def _generate_average_answer(self, question_type: str, template: dict) -> str:
        """生成中等答案（有明显错误）"""
        if question_type == "concept":
            return "栈是一种数据结构，遵循FIFO原则。主要特点是可以在两端进行操作。"  # LIFO说成FIFO
        elif question_type == "calculation":
            return "设 T(n) = T(n-1) + T(n-2)\n所以 T(n) = O(n^2)"  # 结果错误
        elif question_type == "proof":
            return "证明：\n设叶子节点数为 n0，度为2的节点数为 n2。\n因为 n0 = n2，所以结论成立。"  # 推理过程不完整
        else:  # programming
            return "```cpp\nListNode* reverseList(ListNode* head) {\n    ListNode* prev = nullptr;\n    while (head != nullptr) {\n        prev = head;\n        head = head->next;\n    }\n    return prev;\n}\n```"  # 逻辑错误
    
    def _generate_poor_answer(self, question_type: str, template: dict) -> str:
        """生成较差答案（存在重大错误）"""
        if question_type == "concept":
            return "栈是一种数组，可以存储数据。"  # 概念错误
        elif question_type == "calculation":
            return "这个算法很快，时间复杂度是 O(1)。"  # 完全错误
        elif question_type == "proof":
            return "这个结论是对的，因为我们老师讲过。"  # 无证明过程
        else:  # programming
            return "```cpp\nListNode* reverseList(ListNode* head) {\n    return head;\n}\n```"  # 没有实现
    
    def _generate_scoring_points_analysis(self, points: List[str], percentage: float) -> List[dict]:
        """生成评分点分析"""
        analysis = []
        points_per_item = 100 / len(points)
        
        for i, point in enumerate(points):
            # 根据总体得分率生成各个得分点的情况
            if percentage >= 90:
                earned = random.uniform(0.9, 1.0) * points_per_item
                status = "excellent"
            elif percentage >= 75:
                earned = random.uniform(0.7, 0.9) * points_per_item
                status = "good" if i < len(points) - 1 else "average"  # 最后一个点可能有问题
            elif percentage >= 60:
                earned = random.uniform(0.4, 0.8) * points_per_item
                status = "average" if i < len(points) // 2 else "poor"  # 后半部分得分低
            else:
                earned = random.uniform(0.0, 0.5) * points_per_item
                status = "poor"
            
            analysis.append({
                "point": point,
                "earned_percentage": min(100, max(0, earned)),
                "status": status,
                "feedback": self._get_point_feedback(point, status)
            })
        
        return analysis
    
    def _get_point_feedback(self, point: str, status: str) -> str:
        """根据得分点状态生成反馈"""
        feedback_map = {
            "excellent": "✅ 完全正确",
            "good": "🟡 基本正确，有小缺陷",
            "average": "🟠 部分正确，存在错误",
            "poor": "❌ 不正确或缺失"
        }
        return feedback_map.get(status, "⚪ 无评价")
    
    def get_sample_data(self) -> Dict[str, Any]:
        """获取完整的示例数据集"""
        return {
            "student_scores": self.generate_student_scores(50),
            "question_analysis": self.generate_question_analysis(12),
            "assignment_stats": self.generate_assignment_stats()
        }


# 全局数据加载器实例
data_loader = DataLoader()

def load_sample_data() -> Dict[str, Any]:
    """加载示例数据的便捷函数"""
    return data_loader.get_sample_data()

def get_student_scores(count: int = 50) -> List[StudentScore]:
    """获取学生成绩数据的便捷函数"""
    return data_loader.generate_student_scores(count)

def get_question_analysis(count: int = 12) -> List[QuestionAnalysis]:
    """获取题目分析数据的便捷函数"""
    return data_loader.generate_question_analysis(count)

def get_assignment_stats() -> AssignmentStats:
    """获取作业统计数据的便捷函数"""
    return data_loader.generate_assignment_stats()