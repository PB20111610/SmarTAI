"""
评分报告界面 (pages/score_report.py)

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

from frontend_utils.data_loader import StudentScore, load_ai_grading_data, load_mock_data
from frontend_utils.chart_components import create_student_radar_chart

# 页面配置
st.set_page_config(
    page_title="SmarTAI - 评分报告",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

def init_session_state():
    """初始化会话状态"""
    # Check if we have a selected job for AI grading data
    if 'selected_job_id' in st.session_state and st.session_state.selected_job_id:
        # Load AI grading data
        with st.spinner("正在加载AI批改数据..."):
            ai_data = load_ai_grading_data(st.session_state.selected_job_id)
            if "error" not in ai_data:
                st.session_state.ai_grading_data = ai_data
            else:
                st.error(f"加载AI批改数据失败: {ai_data['error']}")
                # Fallback to mock data
                st.session_state.sample_data = load_mock_data()
    else:
        # Load mock data if no job is selected
        if 'sample_data' not in st.session_state:
            st.session_state.sample_data = load_mock_data()

def render_header():
    """渲染页面头部"""
    col1, col2, col3, col4 = st.columns([2, 2, 2, 2])
    
    with col1:
        if st.button("🏠 返回首页", type="secondary"):
            st.switch_page("main.py")
    
    with col2:
        if st.button("📊 批改结果", type="secondary"):
            st.switch_page("pages/grade_results.py")
    
    with col3:
        st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>📊 评分报告</h1>", 
                   unsafe_allow_html=True)
    
    with col4:
        if st.button("📈 可视化分析", type="primary"):
            st.switch_page("pages/visualization.py")

def render_student_selection(students: List[StudentScore]):
    """渲染学生选择界面"""
    st.markdown("## 📋 选择学生查看详细报告")
    
    if not students:
        st.warning("⚠️ 没有学生数据")
        return None
    
    # 按成绩降序排列
    sorted_students = sorted(students, key=lambda x: x.percentage, reverse=True)
    student_options = [f"{s.student_name} ({s.student_id}) - {s.percentage:.1f}% - {s.grade_level}" for s in sorted_students]
    
    selected_option = st.selectbox(
        "选择学生",
        ["请选择学生..."] + student_options,
        help="学生列表按成绩从高到低排序"
    )
    
    if selected_option and selected_option != "请选择学生...":
        selected_id = selected_option.split('(')[1].split(')')[0]
        selected_student = next(s for s in sorted_students if s.student_id == selected_id)
        return selected_student
    
    return None

def render_student_report(student: StudentScore):
    """渲染学生详细报告"""
    st.markdown(f"# 📄 {student.student_name} 的作业报告")
    st.markdown(f"**学号:** {student.student_id} | **提交时间:** {student.submit_time.strftime('%Y-%m-%d %H:%M')}")
    
    # Add PDF export button
    if st.button("📄 导出为PDF"):
        try:
            # Import PDF generator
            from frontend_utils.pdf_generator import generate_student_report
            
            with st.spinner("正在生成PDF报告..."):
                # Generate PDF report
                pdf_path = generate_student_report(student)
                
                # Provide download link
                with open(pdf_path, "rb") as file:
                    st.download_button(
                        label="📥 下载PDF报告",
                        data=file,
                        file_name=f"{student.student_name}_作业报告.pdf",
                        mime="application/pdf",
                        key="download_pdf_student"
                    )
                st.success("PDF报告已生成！点击上方按钮下载。")
        except Exception as e:
            st.error(f"生成PDF报告时出错: {str(e)}")
    
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
        # Use consistent color coding for grade levels
        if student.grade_level == "优秀":
            grade_color = "#10B981"  # green
        elif student.grade_level == "良好":
            grade_color = "#3B82F6"  # blue
        elif student.grade_level == "中等":
            grade_color = "#2E8B57"  # teal
        elif student.grade_level == "及格":
            grade_color = "#F59E0B"  # orange
        else:  # 不及格
            grade_color = "#EF4444"  # red
            
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
    
    # 题目详细信息
    st.markdown("## 📝 题目详情")
    
    if not student.questions:
        st.info("暂无题目详情")
        return
    
    for i, question in enumerate(student.questions, 1):
        score_percentage = (question['score'] / question['max_score']) * 100
        score_color = "#10B981" if score_percentage >= 80 else "#F59E0B" if score_percentage >= 60 else "#EF4444"
        
        # 确保knowledge_points是列表格式
        knowledge_points = question.get('knowledge_points', [])
        if not isinstance(knowledge_points, list):
            knowledge_points = [str(knowledge_points)] if knowledge_points else []
        
        knowledge_points_text = ', '.join(knowledge_points) if knowledge_points else "无"
        
        st.markdown(f"""
        <div style="background: white; padding: 1.5rem; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin: 1rem 0; border-left: 4px solid {score_color};">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                <h3 style="color: #1E3A8A; margin: 0;">📝 题目 {i}: {question['question_id']}</h3>
                <div style="text-align: right;">
                    <h2 style="color: {score_color}; margin: 0;">{question['score']:.1f}/{question['max_score']}</h2>
                    <span style="color: #64748B; font-size: 0.9rem;">({score_percentage:.1f}%)</span>
                </div>
            </div>
            <div style="display: flex; justify-content: space-between; align-items: center; font-size: 0.9rem;">
                <div>
                    <strong>题型:</strong> {question['question_type']}<br>
                    <strong>知识点:</strong> {knowledge_points_text}
                </div>
                <div>
                    <strong>置信度:</strong> {question['confidence']:.1%}
                </div>
            </div>
            {f'<div style="margin-top: 1rem; padding: 0.5rem; background: #F8FAFC; border-radius: 4px;"><strong>反馈:</strong> {question["feedback"]}</div>' if question.get('feedback') else ''}
        </div>
        """, unsafe_allow_html=True)

def main():
    """主函数"""
    # 初始化
    init_session_state()
    
    # 渲染页面
    render_header()
    
    # 获取数据 - 优先使用AI批改数据，如果没有则使用示例数据
    if 'ai_grading_data' in st.session_state and st.session_state.ai_grading_data:
        students = st.session_state.ai_grading_data.get('student_scores', [])
    elif 'sample_data' in st.session_state and st.session_state.sample_data:
        students = st.session_state.sample_data.get('student_scores', [])
    else:
        # Load mock data as fallback
        mock_data = load_mock_data()
        students = mock_data.get('student_scores', [])
    
    # 渲染学生选择
    selected_student = render_student_selection(students)
    
    # 如果选择了学生，显示详细报告
    if selected_student:
        st.markdown("---")
        render_student_report(selected_student)

if __name__ == "__main__":
    main()