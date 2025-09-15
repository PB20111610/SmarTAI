"""
评分报告界面 (pages/score_report.py)

功能包括：
1. 学生作业列表展示
2. 详细评分查看
3. 批量操作
4. 导航功能
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import plotly.express as px
import plotly.graph_objects as go
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode
import base64
import json

# 导入自定义模块
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.data_loader import StudentScore, get_student_scores, load_sample_data
from utils.chart_components import create_student_radar_chart

# 页面配置
st.set_page_config(
    page_title="SmarTAI - 评分报告",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 加载自定义CSS
def load_css():
    """加载自定义CSS样式"""
    try:
        with open("assets/styles.css", "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        # 如果文件不存在，使用内联样式
        st.markdown("""
        <style>
        .main {
            padding: 2rem;
        }
        .student-card {
            background: white;
            padding: 1.5rem;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            margin: 1rem 0;
            border-left: 4px solid #2E8B57;
            transition: all 0.3s ease;
        }
        .student-card:hover {
            box-shadow: 0 8px 15px rgba(0, 0, 0, 0.15);
            transform: translateY(-2px);
        }
        .score-high { color: #10B981; font-weight: bold; }
        .score-medium { color: #F59E0B; font-weight: bold; }
        .score-low { color: #EF4444; font-weight: bold; }
        .confidence-low { 
            background-color: #FEE2E2; 
            color: #991B1B; 
            padding: 0.25rem 0.5rem; 
            border-radius: 0.25rem; 
            animation: pulse 2s infinite;
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.7; }
        }
        .breadcrumb {
            background: white;
            padding: 1rem;
            border-radius: 8px;
            margin-bottom: 1.5rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        </style>
        """, unsafe_allow_html=True)

def init_session_state():
    """初始化会话状态"""
    if 'sample_data' not in st.session_state:
        with st.spinner("加载数据中..."):
            st.session_state.sample_data = load_sample_data()
    
    if 'selected_students' not in st.session_state:
        st.session_state.selected_students = set()
    
    if 'search_query' not in st.session_state:
        st.session_state.search_query = ""
    
    if 'expanded_student' not in st.session_state:
        st.session_state.expanded_student = None

def render_breadcrumb():
    """渲染面包屑导航"""
    st.markdown("""
    <div class="breadcrumb">
        <a href="/" style="text-decoration: none; color: #666;">🏠 首页</a>
        <span style="margin: 0 0.5rem; color: #666;">></span>
        <span style="color: #1E3A8A; font-weight: 600;">📊 评分报告</span>
    </div>
    """, unsafe_allow_html=True)

def render_header():
    """渲染页面头部"""
    col1, col2, col3 = st.columns([2, 3, 2])
    
    with col1:
        if st.button("🏠 返回首页", type="secondary"):
            st.switch_page("main.py")
    
    with col2:
        st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>📊 评分报告</h1>", 
                   unsafe_allow_html=True)
    
    with col3:
        if st.button("📈 可视化分析", type="primary"):
            st.switch_page("pages/visualization.py")

def render_search_and_filters():
    """渲染搜索和筛选控件"""
    col1, col2, col3, col4 = st.columns([3, 2, 2, 2])
    
    with col1:
        search_query = st.text_input(
            "🔍 搜索学生",
            value=st.session_state.search_query,
            placeholder="输入学号或姓名进行搜索...",
            key="search_input"
        )
        st.session_state.search_query = search_query
    
    with col2:
        score_filter = st.selectbox(
            "成绩筛选",
            ["全部", "优秀(90+)", "良好(80-90)", "中等(70-80)", "及格(60-70)", "不及格(<60)"]
        )
    
    with col3:
        review_filter = st.selectbox(
            "复核状态",
            ["全部", "需要复核", "无需复核"]
        )
    
    with col4:
        confidence_filter = st.selectbox(
            "置信度筛选",
            ["全部", "高置信度(85%+)", "中置信度(70-85%)", "低置信度(<70%)"]
        )
    
    return search_query, score_filter, review_filter, confidence_filter

def filter_students(students: List[StudentScore], search_query: str, score_filter: str, 
                   review_filter: str, confidence_filter: str) -> List[StudentScore]:
    """根据筛选条件过滤学生列表"""
    filtered = students.copy()
    
    # 搜索筛选
    if search_query:
        filtered = [s for s in filtered if 
                   search_query.lower() in s.student_name.lower() or 
                   search_query.lower() in s.student_id.lower()]
    
    # 成绩筛选
    if score_filter != "全部":
        if score_filter == "优秀(90+)":
            filtered = [s for s in filtered if s.percentage >= 90]
        elif score_filter == "良好(80-90)":
            filtered = [s for s in filtered if 80 <= s.percentage < 90]
        elif score_filter == "中等(70-80)":
            filtered = [s for s in filtered if 70 <= s.percentage < 80]
        elif score_filter == "及格(60-70)":
            filtered = [s for s in filtered if 60 <= s.percentage < 70]
        elif score_filter == "不及格(<60)":
            filtered = [s for s in filtered if s.percentage < 60]
    
    # 复核状态筛选
    if review_filter != "全部":
        if review_filter == "需要复核":
            filtered = [s for s in filtered if s.need_review]
        elif review_filter == "无需复核":
            filtered = [s for s in filtered if not s.need_review]
    
    # 置信度筛选
    if confidence_filter != "全部":
        if confidence_filter == "高置信度(85%+)":
            filtered = [s for s in filtered if s.confidence_score >= 0.85]
        elif confidence_filter == "中置信度(70-85%)":
            filtered = [s for s in filtered if 0.70 <= s.confidence_score < 0.85]
        elif confidence_filter == "低置信度(<70%)":
            filtered = [s for s in filtered if s.confidence_score < 0.70]
    
    return filtered

def get_score_color_class(percentage: float) -> str:
    """根据分数百分比获取CSS类名"""
    if percentage >= 85:
        return "score-high"
    elif percentage >= 70:
        return "score-medium"
    else:
        return "score-low"

def get_confidence_display(confidence: float) -> str:
    """获取置信度显示"""
    if confidence < 0.70:
        return f'<span class="confidence-low">低置信度 {confidence:.1%}</span>'
    elif confidence < 0.85:
        return f'<span style="color: #F59E0B;">中置信度 {confidence:.1%}</span>'
    else:
        return f'<span style="color: #10B981;">高置信度 {confidence:.1%}</span>'

def render_student_card(student: StudentScore, index: int):
    """渲染学生成绩卡片"""
    score_class = get_score_color_class(student.percentage)
    confidence_display = get_confidence_display(student.confidence_score)
    
    # 检查是否展开
    is_expanded = st.session_state.expanded_student == student.student_id
    expand_text = "收起" if is_expanded else "展开详情"
    
    # 卡片容器
    with st.container():
        # 创建卡片内容
        card_html = f"""
        <div class="student-card">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                <div>
                    <h3 style="margin: 0; color: #1E3A8A;">{student.student_name}</h3>
                    <span style="background: #F1F5F9; padding: 0.25rem 0.5rem; border-radius: 0.25rem; font-size: 0.875rem; color: #64748B;">
                        {student.student_id}
                    </span>
                </div>
                <div style="text-align: right;">
                    <div class="{score_class}" style="font-size: 1.5rem;">
                        {student.total_score:.1f}/{student.max_score}
                    </div>
                    <div style="font-size: 0.875rem; color: #64748B;">
                        {student.percentage:.1f}% ({student.grade_level})
                    </div>
                </div>
            </div>
            
            <div style="display: flex; justify-content: space-between; align-items: center; font-size: 0.875rem;">
                <div>
                    <span style="color: #64748B;">提交时间:</span>
                    <span>{student.submit_time.strftime('%Y-%m-%d %H:%M')}</span>
                </div>
                <div>
                    {confidence_display}
                    {'<span style="background: #FEE2E2; color: #991B1B; padding: 0.25rem 0.5rem; border-radius: 0.25rem; margin-left: 0.5rem;">需复核</span>' if student.need_review else ''}
                </div>
            </div>
        </div>
        """
        
        st.markdown(card_html, unsafe_allow_html=True)
        
        # 展开/收起按钮
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            expand_key = f"expand_{index}"
            if st.button(expand_text, key=expand_key, help="点击查看详细信息", 
                        type="secondary", use_container_width=True):
                if st.session_state.expanded_student == student.student_id:
                    st.session_state.expanded_student = None
                else:
                    st.session_state.expanded_student = student.student_id
                st.rerun()
        
        # 如果是展开状态，显示详细信息
        if is_expanded:
            render_student_details(student)

def render_individual_student_report(student: StudentScore):
    """渲染个人学生详细报告"""
    st.markdown(f"# 📄 {student.student_name} 的作业批改报告")
    st.markdown(f"**学号:** {student.student_id} | **提交时间:** {student.submit_time.strftime('%Y-%m-%d %H:%M')}")
    
    # 顶部成绩概览
    render_top_overview_section(student)
    
    # 逐题详细报告
    st.markdown("---")
    st.markdown("## 📝 逐题详细报告")
    
    for i, question in enumerate(student.questions, 1):
        render_question_detailed_report(question, i)
    
    # 编辑区域
    render_manual_review_section(student)

def render_top_overview_section(student: StudentScore):
    """渲染顶部总体得分概览"""
    st.markdown("### 🏆 总体得分概览")
    
    # 主要得分指标
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        score_color = "#10B981" if student.percentage >= 85 else "#F59E0B" if student.percentage >= 70 else "#EF4444"
        st.markdown(f"""
        <div style="text-align: center; padding: 1.5rem; background: white; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); border-left: 4px solid {score_color};">
            <h1 style="color: {score_color}; margin: 0; font-size: 2.5rem;">{student.total_score:.1f}</h1>
            <h3 style="color: {score_color}; margin: 0.5rem 0; font-size: 1.2rem;">/{student.max_score}</h3>
            <p style="margin: 0; color: #64748B; font-weight: 600;">总分</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div style="text-align: center; padding: 1.5rem; background: white; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            <h1 style="color: {score_color}; margin: 0; font-size: 2.5rem;">{student.percentage:.1f}%</h1>
            <p style="margin: 0; color: #64748B; font-weight: 600;">百分比</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        grade_color = "#10B981" if student.grade_level in ["优秀", "良好"] else "#F59E0B" if student.grade_level == "中等" else "#EF4444"
        st.markdown(f"""
        <div style="text-align: center; padding: 1.5rem; background: white; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            <h1 style="color: {grade_color}; margin: 0; font-size: 2rem;">{student.grade_level}</h1>
            <p style="margin: 0; color: #64748B; font-weight: 600;">成绩等级</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        conf_color = "#10B981" if student.confidence_score >= 0.85 else "#F59E0B" if student.confidence_score >= 0.70 else "#EF4444"
        confidence_text = "高置信度" if student.confidence_score >= 0.85 else "中置信度" if student.confidence_score >= 0.70 else "低置信度"
        st.markdown(f"""
        <div style="text-align: center; padding: 1.5rem; background: white; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            <h1 style="color: {conf_color}; margin: 0; font-size: 2rem;">{student.confidence_score:.0%}</h1>
            <p style="margin: 0; color: {conf_color}; font-weight: 600; font-size: 0.9rem;">{confidence_text}</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("")
    
    # 得分构成分析
    st.markdown("#### 📊 得分构成分析")
    
    # 按题目类型统计得分
    type_scores = {}
    type_max_scores = {}
    type_counts = {}
    
    for question in student.questions:
        qtype = question['question_type']
        if qtype not in type_scores:
            type_scores[qtype] = 0
            type_max_scores[qtype] = 0
            type_counts[qtype] = 0
        
        type_scores[qtype] += question['score']
        type_max_scores[qtype] += question['max_score']
        type_counts[qtype] += 1
    
    # 显示各类型得分
    type_names = {
        'concept': '概念理解',
        'calculation': '计算能力',
        'proof': '证明推理', 
        'programming': '编程实现'
    }
    
    type_cols = st.columns(len(type_scores))
    for i, (qtype, score) in enumerate(type_scores.items()):
        with type_cols[i]:
            max_score = type_max_scores[qtype]
            percentage = (score / max_score) * 100 if max_score > 0 else 0
            type_color = "#10B981" if percentage >= 80 else "#F59E0B" if percentage >= 60 else "#EF4444"
            
            st.markdown(f"""
            <div style="text-align: center; padding: 1rem; background: #F8FAFC; border-radius: 6px; border: 1px solid #E2E8F0;">
                <h3 style="color: {type_color}; margin: 0;">{score:.1f}/{max_score}</h3>
                <p style="margin: 0.25rem 0; color: #64748B; font-size: 0.9rem;">{type_names.get(qtype, qtype)}</p>
                <p style="margin: 0; color: {type_color}; font-weight: 600; font-size: 0.8rem;">{percentage:.1f}% ({type_counts[qtype]}题)</p>
            </div>
            """, unsafe_allow_html=True)
    
    # 及格线提示
    passing_score = 60
    st.markdown("#### 🎯 成绩评价")
    
    if student.percentage < passing_score:
        st.error(f"⚠️ **未达及格线**: 当前成绩 {student.percentage:.1f}%，低于及格线 {passing_score}%，差距 {passing_score - student.percentage:.1f} 个百分点")
        st.markdown("💡 **建议**: 加强基础知识复习，重点关注错误较多的题型")
    elif student.percentage < 70:
        st.warning(f"📝 **刚过及格线**: 当前成绩 {student.percentage:.1f}%，超出及格线 {student.percentage - passing_score:.1f} 个百分点，仍有较大提升空间")
        st.markdown("💡 **建议**: 巩固已掌握的知识点，逐步提高解题准确率")
    elif student.percentage < 85:
        st.info(f"👍 **表现良好**: 当前成绩 {student.percentage:.1f}%，超出及格线 {student.percentage - passing_score:.1f} 个百分点")
        st.markdown("💡 **建议**: 继续保持，向优秀水平冲刺")
    else:
        st.success(f"🎉 **表现优秀**: 当前成绩 {student.percentage:.1f}%，超出及格线 {student.percentage - passing_score:.1f} 个百分点")
        st.markdown("💡 **建议**: 保持优秀水平，可以挑战更难的题目")

def render_question_detailed_report(question: Dict[str, Any], question_num: int):
    """渲染单个题目的详细报告"""
    
    # 题目标题区域
    score_percentage = (question['score'] / question['max_score']) * 100
    score_color = "#10B981" if score_percentage >= 80 else "#F59E0B" if score_percentage >= 60 else "#EF4444"
    
    # 基本信息和置信度显示
    question_type_text = question['question_type']
    knowledge_points_text = ', '.join(question['knowledge_points'])
    confidence_value = question['confidence']
    
    if confidence_value >= 0.85:
        confidence_color = '#10B981'
    elif confidence_value >= 0.70:
        confidence_color = '#F59E0B'
    else:
        confidence_color = '#EF4444'
    
    # 题目标题区域 - 使用简单的HTML结构
    # 主要题目信息框
    header_html = f"""
    <div style="background: white; padding: 1.5rem; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin: 1rem 0; border-left: 4px solid {score_color};">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
            <h3 style="color: #1E3A8A; margin: 0;">📝 题目 {question_num}: {question['question_id']}</h3>
            <div style="text-align: right;">
                <h2 style="color: {score_color}; margin: 0;">{question['score']:.1f}/{question['max_score']}</h2>
                <span style="color: #64748B; font-size: 0.9rem;">({score_percentage:.1f}%)</span>
            </div>
        </div>
    </div>
    """
    
    st.markdown(header_html, unsafe_allow_html=True)
    
    # 题目详细信息使用Streamlit原生组件
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"**🎨 题型:** {question_type_text}")
    
    with col2:
        st.markdown(f"**📚 知识点:** {knowledge_points_text}")
    
    with col3:
        confidence_text = f"{confidence_value:.1%}"
        if confidence_value >= 0.85:
            st.success(f"**🟢 置信度:** {confidence_text}")
        elif confidence_value >= 0.70:
            st.warning(f"**🟡 置信度:** {confidence_text}")
        else:
            st.error(f"**🔴 置信度:** {confidence_text}")
    
    st.markdown("")
    
    # 题目内容和学生答案展示（可收起）
    with st.expander("📝 查看题目内容和学生答案", expanded=False):
        # 题目内容
        if 'question_content' in question:
            st.markdown("#### 📆 题目内容")
            st.markdown(f"""
            <div style="background: #F8FAFC; padding: 1rem; border-radius: 6px; border-left: 3px solid #3B82F6; margin: 0.5rem 0;">
                <div style="color: #374151; line-height: 1.6;">{question['question_content']}</div>
            </div>
            """, unsafe_allow_html=True)
        
        # 标准答案
        if 'standard_answer' in question:
            st.markdown("#### 🎯 标准答案")
            st.markdown(f"""
            <div style="background: #F0FDF4; padding: 1rem; border-radius: 6px; border-left: 3px solid #10B981; margin: 0.5rem 0;">
                <div style="color: #374151; line-height: 1.6;">{question['standard_answer']}</div>
            </div>
            """, unsafe_allow_html=True)
        
        # 学生答案
        if 'student_answer' in question:
            st.markdown("#### ✍️ 学生答案")
            answer_bg_color = "#F0FDF4" if score_percentage >= 80 else "#FEF3C7" if score_percentage >= 60 else "#FEE2E2"
            answer_border_color = "#10B981" if score_percentage >= 80 else "#F59E0B" if score_percentage >= 60 else "#EF4444"
            
            st.markdown(f"""
            <div style="background: {answer_bg_color}; padding: 1rem; border-radius: 6px; border-left: 3px solid {answer_border_color}; margin: 0.5rem 0;">
                <div style="color: #374151; line-height: 1.6;">{question['student_answer']}</div>
            </div>
            """, unsafe_allow_html=True)
    
    # 评分细则和判分依据
    if 'grading_rules' in question:
        st.markdown("##### 📋 评分细则与判分依据")
        grading_rules = question['grading_rules']
        
        # 评分标准
        st.markdown("**评分标准:**")
        for criterion in grading_rules['scoring_criteria']:
            score_pct = criterion['points'] * 100
            criterion_color = "#10B981" if score_pct >= 80 else "#F59E0B" if score_pct >= 60 else "#EF4444"
            st.markdown(f"- **{criterion['criterion']}** (权重 {criterion['weight']:.0%}): "
                       f"<span style='color: {criterion_color}; font-weight: bold;'>{score_pct:.0f}分</span> - {criterion['description']}", 
                       unsafe_allow_html=True)
        
        # 命中的自动规则
        if grading_rules.get('auto_rules_hit'):
            st.markdown("**命中的评分规则:**")
            for rule in grading_rules['auto_rules_hit']:
                st.markdown(f"- ✅ {rule}")
        
        # 模型输出简要说明
        if 'model_output' in question:
            model_output = question['model_output']
            with st.expander("🤖 AI模型判分依据", expanded=False):
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**模型:** {model_output['model_name']}")
                    st.markdown(f"**处理时间:** {model_output['processing_time']}")
                with col2:
                    st.markdown(f"**推理tokens:** {model_output['reasoning_tokens']:,}")
                    st.markdown(f"**置信度:** {question['confidence']:.1%}")
                
                st.markdown("**模型分析摘要:**")
                st.info(model_output['output_summary'])
                
                # 关键日志片段
                if model_output.get('log_entries'):
                    with st.expander("📄 关键运行日志片段"):
                        for log_entry in model_output['log_entries'][:3]:  # 只显示前3条关键日志
                            if "[WARN]" in log_entry or "[ERROR]" in log_entry:
                                st.warning(log_entry)
                            else:
                                st.code(log_entry, language=None)
    
    # 逐步点评与得分分析（对于有步骤的题目）
    if 'step_analysis' in question and question['step_analysis']:
        st.markdown("##### 🔍 逐步点评与得分分析")
        
        for step_idx, step in enumerate(question['step_analysis']):
            # 步骤标题和状态
            status_icon = "✅" if step['is_correct'] else "❌"
            step_color = "#10B981" if step['is_correct'] else "#EF4444"
            
            # 高亮错误步骤
            if step.get('highlight', False) or not step['is_correct']:
                step_bg = "#FEE2E2" if not step['is_correct'] else "#F0FDF4"
                border_color = "#EF4444" if not step['is_correct'] else "#10B981"
            else:
                step_bg = "#F8FAFC"
                border_color = "#E2E8F0"
            
            # 使用简单的HTML结构
            step_html = f"""
            <div style="background: {step_bg}; padding: 1rem; border-radius: 6px; border-left: 3px solid {border_color}; margin: 0.5rem 0; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                    <h4 style="color: #1E3A8A; margin: 0; font-size: 1.1rem;">{status_icon} 步骤 {step['step_number']}: {step['step_title']}</h4>
                    <span style="color: {step_color}; font-weight: bold; font-size: 1rem;">{step['points_earned']:.1f}/{step['max_points']:.1f}分</span>
                </div>
            </div>
            """
            
            st.markdown(step_html, unsafe_allow_html=True)
            
            # 反馈信息使用单独的组件
            if step['feedback']:
                if step['is_correct']:
                    st.success(f"💬 **反馈:** {step['feedback']}")
                else:
                    st.error(f"💬 **反馈:** {step['feedback']}")
            
            # 错误类型标签
            if step.get('error_type') and not step['is_correct']:
                st.markdown(f"""
                <div style="margin: 0.25rem 0 0.5rem 1rem;">
                    <span style="background: #FEE2E2; color: #991B1B; padding: 0.25rem 0.75rem; border-radius: 12px; font-size: 0.8rem; font-weight: 600;">
                        🏷️ {step['error_type']}
                    </span>
                </div>
                """, unsafe_allow_html=True)
    
    # 总体反馈
    if question.get('feedback'):
        st.markdown("##### 💬 总体评语")
        feedback_color = "#10B981" if score_percentage >= 80 else "#F59E0B" if score_percentage >= 60 else "#EF4444"
        st.markdown(f"""
        <div style="background: #F8FAFC; padding: 1rem; border-radius: 6px; border-left: 3px solid {feedback_color};">
            <p style="margin: 0; color: #374151; font-style: italic;">"{question['feedback']}"</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")

def render_manual_review_section(student: StudentScore):
    """渲染人工复核修改区域"""
    st.markdown("## ✏️ 人工复核与评分修改")
    
    # 复核提示
    if student.need_review:
        st.error("🔴 **此份作业需要人工复核** - 系统检测到低置信度评分，建议仔细检查")
    else:
        st.success("✅ **评分置信度良好** - 无需强制复核，但您仍可进行人工调整")
    
    # 复核建议
    review_questions = [q for q in student.questions if q.get('review_notes', {}).get('needs_review', False)]
    if review_questions:
        st.markdown("### 🔍 需要重点复核的题目")
        
        for question in review_questions:
            review_notes = question['review_notes']
            priority_color = "#EF4444" if review_notes['review_priority'] == 'High' else "#F59E0B" if review_notes['review_priority'] == 'Medium' else "#10B981"
            
            with st.expander(f"🔍 {question['question_id']} - {review_notes['review_priority']} Priority", expanded=review_notes['review_priority'] == 'High'):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**复核原因:**")
                    for reason in review_notes['review_reasons']:
                        if reason:
                            st.markdown(f"- {reason}")
                
                with col2:
                    st.markdown("**建议操作:**")
                    for action in review_notes['suggested_actions']:
                        if action:
                            st.markdown(f"- {action}")
                
                st.markdown(f"**预计复核时间:** {review_notes['estimated_review_time']}")
    
    # 评分编辑区域
    st.markdown("### ✏️ 评分编辑")
    
    with st.form(f"edit_scores_{student.student_id}"):
        st.markdown("**⚠️ 注意**: 修改评分将影响最终成绩，请谨慎操作并填写修改理由")
        
        # 总体评语编辑
        overall_comment = st.text_area(
            "总体评语",
            value=f"该学生本次作业得分 {student.total_score:.1f}/{student.max_score}，成绩等级为{student.grade_level}。",
            height=80,
            help="请提供对学生整体表现的评价"
        )
        
        # 逐题分数和评语编辑
        st.markdown("**题目分数调整**")
        
        modified_total = 0
        
        for i, question in enumerate(student.questions):
            st.markdown(f"**{question['question_id']}** ({question['question_type']})")
            
            col1, col2, col3 = st.columns([1, 2, 1])
            
            with col1:
                new_score = st.number_input(
                    f"得分",
                    min_value=0.0,
                    max_value=float(question['max_score']),
                    value=float(question['score']),
                    step=0.1,
                    format="%.1f",
                    key=f"manual_score_{student.student_id}_{i}",
                    help=f"满分: {question['max_score']}"
                )
                modified_total += new_score
            
            with col2:
                new_feedback = st.text_area(
                    f"评语",
                    value=question.get('feedback', ''),
                    height=60,
                    key=f"manual_feedback_{student.student_id}_{i}",
                    help="请提供具体的反馈意见"
                )
            
            with col3:
                st.markdown(f"**原分数:** {question['score']:.1f}")
                score_diff = new_score - question['score']
                if score_diff > 0:
                    st.success(f"+{score_diff:.1f}")
                elif score_diff < 0:
                    st.error(f"{score_diff:.1f}")
                else:
                    st.info("无变化")
        
        # 显示修改后总分
        total_diff = modified_total - student.total_score
        modified_percentage = (modified_total / student.max_score) * 100
        
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown(f"**原总分:** {student.total_score:.1f}/{student.max_score} ({student.percentage:.1f}%)")
        
        with col2:
            score_color = "#10B981" if modified_percentage >= 85 else "#F59E0B" if modified_percentage >= 70 else "#EF4444"
            st.markdown(f"**修改后总分:** <span style='color: {score_color}; font-weight: bold;'>{modified_total:.1f}/{student.max_score} ({modified_percentage:.1f}%)</span>", unsafe_allow_html=True)
        
        with col3:
            if total_diff > 0:
                st.success(f"变化: +{total_diff:.1f}分")
            elif total_diff < 0:
                st.error(f"变化: {total_diff:.1f}分")
            else:
                st.info("变化: 无")
        
        # 修改理由
        modification_reason = st.text_area(
            "修改理由 *",
            placeholder="请详细说明修改评分的理由，此信息将记录在系统中用于审计追踪...",
            height=80,
            help="必填项：请说明为什么要修改评分"
        )
        
        # 提交按钮
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col1:
            if st.form_submit_button("💾 保存修改", type="primary", use_container_width=True):
                if not modification_reason.strip():
                    st.error("❌ 请填写修改理由")
                else:
                    # 这里实际应用中需要保存到数据库
                    st.success("✅ 评分修改已保存！")
                    st.info(f"📝 修改理由已记录: {modification_reason}")
                    st.balloons()
        
        with col2:
            if st.form_submit_button("🔄 重置为原始评分", type="secondary", use_container_width=True):
                st.info("🔄 评分已重置到原始状态")
                st.rerun()
        
        with col3:
            if st.form_submit_button("📄 生成修改报告", type="secondary", use_container_width=True):
                with st.spinner("生成修改报告中..."):
                    import time
                    time.sleep(1.5)
                st.success("✅ 修改报告已生成并发送给相关人员")
    """渲染学生详细信息"""

def main():
    """主函数"""
    # 加载CSS和初始化
    load_css()
    init_session_state()
    
    # 渲染页面
    render_breadcrumb()
    render_header()
    
    # 获取数据
    students = st.session_state.sample_data['student_scores']
    
    # 新的布局：学生选择 + 报告展示
    render_student_selection_interface(students)

def render_student_selection_interface(students: List[StudentScore]):
    """渲染学生选择和报告查看界面"""
    st.markdown("## 📋 学生作业批改报告查阅系统")
    
    # 中间栏学生选择区域
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("### 🔍 选择学生查看报告")
        
        # 搜索方式选择 - 将列表选择放在第一位作为默认选项
        search_method = st.radio(
            "查找方式",
            ["从列表选择", "按学号查找", "按姓名查找"],
            help="选择您希望的学生查找方式",
            horizontal=True
        )
        
        selected_student = None
        
        if search_method == "从列表选择":  # 默认选项
            # 按成绩降序排列，方便查看高分学生
            sorted_students = sorted(students, key=lambda x: x.percentage, reverse=True)
            student_options = [f"{s.student_name} ({s.student_id}) - {s.percentage:.1f}% - {s.grade_level}" for s in sorted_students]
            selected_option = st.selectbox(
                "选择学生",
                ["请选择学生..."] + student_options,
                help="学生列表按成绩从高到低排序，点击下拉菜单选择学生"
            )
            if selected_option and selected_option != "请选择学生...":
                selected_id = selected_option.split('(')[1].split(')')[0]
                selected_student = next(s for s in sorted_students if s.student_id == selected_id)
        
        elif search_method == "按学号查找":
            student_id = st.text_input(
                "输入学号",
                placeholder="例如：20240001",
                help="输入完整学号进行精确查找"
            )
            if student_id:
                selected_student = next((s for s in students if s.student_id == student_id), None)
                if not selected_student:
                    st.error(f"❌ 未找到学号为 {student_id} 的学生")
        
        elif search_method == "按姓名查找":
            student_name = st.text_input(
                "输入姓名",
                placeholder="例如：张三",
                help="支持模糊查找，输入部分姓名即可"
            )
            if student_name:
                matching_students = [s for s in students if student_name in s.student_name]
                if matching_students:
                    if len(matching_students) == 1:
                        selected_student = matching_students[0]
                    else:
                        st.info(f"找到 {len(matching_students)} 个匹配的学生，请从下方选择：")
                        student_options = [f"{s.student_name} ({s.student_id})" for s in matching_students]
                        selected_option = st.selectbox("选择学生", student_options)
                        if selected_option:
                            selected_id = selected_option.split('(')[1].split(')')[0]
                            selected_student = next(s for s in matching_students if s.student_id == selected_id)
                else:
                    st.error(f"❌ 未找到姓名包含 '{student_name}' 的学生")
        
        # 显示选择结果
        if selected_student:
            st.success(f"✅ 已选择学生：{selected_student.student_name} ({selected_student.student_id})")
            
            # 快速预览
            with st.container():
                preview_col1, preview_col2, preview_col3 = st.columns(3)
                with preview_col1:
                    st.metric("总分", f"{selected_student.total_score:.1f}/{selected_student.max_score}")
                with preview_col2:
                    st.metric("成绩等级", selected_student.grade_level)
                with preview_col3:
                    review_status = "需要复核" if selected_student.need_review else "无需复核"
                    st.metric("复核状态", review_status)
    
    # 显示选中学生的详细报告
    if selected_student:
        st.markdown("---")
        render_individual_student_report(selected_student)

if __name__ == "__main__":
    main()