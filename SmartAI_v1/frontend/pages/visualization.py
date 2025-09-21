"""
可视化分析界面 (pages/visualization.py)

简化版本，专注于核心成绩展示功能
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import plotly.express as px
import plotly.graph_objects as go

# 导入自定义模块
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Use the updated data loader that can handle AI grading data
from frontend_utils.data_loader import StudentScore, QuestionAnalysis, AssignmentStats, load_ai_grading_data
from frontend_utils.chart_components import (
    create_score_distribution_chart, create_grade_pie_chart
)

# 页面配置
st.set_page_config(
    page_title="SmarTAI - 成绩展示",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

def init_session_state():
    """初始化会话状态"""
    # Check if we have a selected job for AI grading data
    if 'selected_job_id' in st.session_state and st.session_state.selected_job_id:
        # Load AI grading data
        if 'ai_grading_data' not in st.session_state:
            with st.spinner("正在加载AI批改数据..."):
                st.session_state.ai_grading_data = load_ai_grading_data(st.session_state.selected_job_id)
    else:
        # Load sample data if no job is selected
        if 'sample_data' not in st.session_state:
            with st.spinner("加载数据中..."):
                st.session_state.sample_data = create_default_data()

def create_default_data():
    """创建默认数据用于演示"""
    # Create default student scores
    students = [
        StudentScore(
            student_id="S001",
            student_name="张三",
            total_score=85,
            max_score=100,
            submit_time=datetime.now(),
            need_review=False,
            confidence_score=0.92
        ),
        StudentScore(
            student_id="S002",
            student_name="李四",
            total_score=72,
            max_score=100,
            submit_time=datetime.now(),
            need_review=True,
            confidence_score=0.78
        ),
        StudentScore(
            student_id="S003",
            student_name="王五",
            total_score=93,
            max_score=100,
            submit_time=datetime.now(),
            need_review=False,
            confidence_score=0.95
        )
    ]
    
    # Create default assignment stats
    assignment_stats = AssignmentStats(
        assignment_id="DEFAULT",
        assignment_name="示例作业",
        total_students=3,
        submitted_count=3,
        avg_score=83.3,
        max_score=93,
        min_score=72,
        std_score=10.5,
        pass_rate=100,
        question_count=2,
        create_time=datetime.now()
    )
    
    return {
        "student_scores": students,
        "assignment_stats": assignment_stats
    }

def render_header():
    """渲染页面头部"""
    col1, col2, col3 = st.columns([2, 3, 2])
    
    with col1:
        if st.button("🏠 返回首页", type="secondary"):
            st.switch_page("main.py")
    
    with col2:
        st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>📈 成绩展示</h1>", 
                   unsafe_allow_html=True)
    
    with col3:
        if st.button("📊 评分报告", type="primary"):
            st.switch_page("pages/score_report.py")

def render_statistics_overview(students: List[StudentScore], assignment_stats: AssignmentStats):
    """渲染统计概览"""
    st.markdown("## 📊 成绩统计概览")
    
    # 计算统计数据
    if not students:  # 处理空数据情况
        st.warning("⚠️ 没有数据可显示")
        return
    
    scores = [s.percentage for s in students]
    avg_score = np.mean(scores)
    max_score = np.max(scores)
    min_score = np.min(scores)
    std_score = np.std(scores)
    pass_rate = len([s for s in scores if s >= 60]) / len(scores) * 100 if scores else 0
    excellence_rate = len([s for s in scores if s >= 85]) / len(scores) * 100 if scores else 0
    
    # 显示统计卡片
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    with col1:
        st.markdown(f"""
        <div style="background: white; padding: 1.5rem; border-radius: 10px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); text-align: center; border-top: 4px solid #1E3A8A;">
            <div style="font-size: 2.5rem; font-weight: 700; color: #1E3A8A; margin-bottom: 0.25rem;">{len(students)}</div>
            <div style="font-size: 0.875rem; color: #64748B; text-transform: uppercase; font-weight: 600;">提交人数</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div style="background: white; padding: 1.5rem; border-radius: 10px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); text-align: center; border-top: 4px solid #1E3A8A;">
            <div style="font-size: 2.5rem; font-weight: 700; color: #1E3A8A; margin-bottom: 0.25rem;">{avg_score:.1f}%</div>
            <div style="font-size: 0.875rem; color: #64748B; text-transform: uppercase; font-weight: 600;">平均分</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div style="background: white; padding: 1.5rem; border-radius: 10px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); text-align: center; border-top: 4px solid #1E3A8A;">
            <div style="font-size: 2.5rem; font-weight: 700; color: #1E3A8A; margin-bottom: 0.25rem;">{max_score:.1f}%</div>
            <div style="font-size: 0.875rem; color: #64748B; text-transform: uppercase; font-weight: 600;">最高分</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div style="background: white; padding: 1.5rem; border-radius: 10px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); text-align: center; border-top: 4px solid #1E3A8A;">
            <div style="font-size: 2.5rem; font-weight: 700; color: #1E3A8A; margin-bottom: 0.25rem;">{min_score:.1f}%</div>
            <div style="font-size: 0.875rem; color: #64748B; text-transform: uppercase; font-weight: 600;">最低分</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col5:
        st.markdown(f"""
        <div style="background: white; padding: 1.5rem; border-radius: 10px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); text-align: center; border-top: 4px solid #1E3A8A;">
            <div style="font-size: 2.5rem; font-weight: 700; color: #1E3A8A; margin-bottom: 0.25rem;">{pass_rate:.1f}%</div>
            <div style="font-size: 0.875rem; color: #64748B; text-transform: uppercase; font-weight: 600;">及格率</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col6:
        st.markdown(f"""
        <div style="background: white; padding: 1.5rem; border-radius: 10px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); text-align: center; border-top: 4px solid #1E3A8A;">
            <div style="font-size: 2.5rem; font-weight: 700; color: #1E3A8A; margin-bottom: 0.25rem;">{excellence_rate:.1f}%</div>
            <div style="font-size: 0.875rem; color: #64748B; text-transform: uppercase; font-weight: 600;">优秀率</div>
        </div>
        """, unsafe_allow_html=True)

def render_student_table(students: List[StudentScore]):
    """渲染学生表格"""
    st.markdown("## 📋 学生成绩列表")
    
    if not students:
        st.warning("⚠️ 没有学生数据")
        return
    
    # 准备表格数据
    data = []
    for student in students:
        data.append({
            "学号": student.student_id,
            "姓名": student.student_name,
            "总分": f"{student.total_score:.1f}/{student.max_score}",
            "百分比": f"{student.percentage:.1f}%",
            "等级": student.grade_level,
            "提交时间": student.submit_time.strftime('%Y-%m-%d %H:%M'),
            "置信度": f"{student.confidence_score:.1%}",
            "需复核": "是" if student.need_review else "否"
        })
    
    df = pd.DataFrame(data)
    
    # 显示表格
    st.dataframe(df, use_container_width=True)

def render_charts(students: List[StudentScore]):
    """渲染图表"""
    st.markdown("## 📈 成绩分布图表")
    
    if not students:
        st.warning("⚠️ 没有数据可显示")
        return
    
    try:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 成绩分布直方图")
            fig1 = create_score_distribution_chart(students)
            st.plotly_chart(fig1, use_container_width=True)
        
        with col2:
            st.markdown("### 成绩等级分布")
            fig2 = create_grade_pie_chart(students)
            st.plotly_chart(fig2, use_container_width=True)
    except Exception as e:
        st.error(f"生成图表时出错: {str(e)}")

def main():
    """主函数"""
    # 初始化
    init_session_state()
    
    # 渲染页面
    render_header()
    
    # 获取数据 - 优先使用AI批改数据，如果没有则使用示例数据
    if 'ai_grading_data' in st.session_state and st.session_state.ai_grading_data:
        data = st.session_state.ai_grading_data
    else:
        data = st.session_state.sample_data
    
    students = data['student_scores']
    assignment_stats = data['assignment_stats']
    
    # 渲染各个模块
    render_statistics_overview(students, assignment_stats)
    
    st.markdown("---")
    
    render_student_table(students)
    
    st.markdown("---")
    
    render_charts(students)

if __name__ == "__main__":
    main()
