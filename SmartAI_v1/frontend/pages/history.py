"""
历史批改记录 (pages/history.py)

提供完整的历史批改记录管理功能，包括：
1. 暂存功能：上传作业后可以暂存，预览识别结果并手工调整
2. 批改记录查看：查看已完成的批改记录和可视化分析
3. 记录管理：删除、编辑暂存记录
"""

import streamlit as st
import requests
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import pandas as pd
from utils import *

# Import data loader for AI grading data
from frontend_utils.data_loader import load_ai_grading_data

# 页面配置
st.set_page_config(
    page_title="SmarTAI - 历史批改记录",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 初始化会话状态
initialize_session_state()
load_custom_css()

def init_storage_state():
    """初始化存储状态"""
    if 'completed_records' not in st.session_state:
        st.session_state.completed_records = {}  # 完成记录
    
    # Initialize mock data for consistency with other pages
    if 'sample_data' not in st.session_state:
        from frontend_utils.data_loader import load_mock_data
        with st.spinner("加载模拟数据..."):
            st.session_state.sample_data = load_mock_data()

def render_header():
    """渲染页面头部"""
    col1, col2, col3 = st.columns([2, 3, 2])
    
    with col1:
        if st.button("🏠 返回首页", type="secondary"):
            st.switch_page("main.py")
    
    with col2:
        st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>📚 历史批改记录</h1>", 
                   unsafe_allow_html=True)
    
    with col3:
        if st.button("🔄 刷新记录", type="primary"):
            sync_completed_records()
            st.success("记录已刷新！")
            st.rerun()

def sync_completed_records():
    """同步已完成的批改记录"""
    if "jobs" in st.session_state and st.session_state.jobs:
        # Create a copy of the keys to avoid "dictionary changed size during iteration" error
        job_ids = list(st.session_state.jobs.keys())
        for job_id in job_ids:
            # Check if job_id still exists (in case it was deleted during iteration)
            if job_id not in st.session_state.jobs:
                continue
                
            task_info = st.session_state.jobs[job_id]
            
            # Skip mock jobs entirely to prevent continuous polling
            if job_id.startswith("MOCK_JOB_"):
                # Remove mock jobs from session state to prevent continuous polling
                if job_id in st.session_state.jobs:
                    del st.session_state.jobs[job_id]
                continue
                
            # Check if this is a mock job
            is_mock = task_info.get("is_mock", False)
            
            if is_mock:
                # Remove mock jobs from session state to prevent continuous polling
                if job_id in st.session_state.jobs:
                    del st.session_state.jobs[job_id]
                continue



def render_tabs():
    """渲染主要标签页"""
    tab1, tab2 = st.tabs(["✅ 已完成批改", "📊 统计概览"])
    
    with tab1:
        render_completed_records()
    
    with tab2:
        render_statistics_overview()

def render_mock_data_preview():
    """渲染模拟数据预览"""
    st.markdown("## 🔍 模拟数据预览")
    st.markdown("这里显示与评分报告和可视化分析页面一致的模拟数据。")
    
    # Load mock data
    from frontend_utils.data_loader import load_mock_data
    mock_data = st.session_state.get('sample_data', load_mock_data())
    
    students = mock_data.get('student_scores', [])
    assignment_stats = mock_data.get('assignment_stats', None)
    question_analysis = mock_data.get('question_analysis', [])
    
    if not students:
        st.warning("暂无模拟数据")
        return
    
    # Display assignment stats
    if assignment_stats:
        st.markdown(f"### 作业统计信息")
        st.markdown(f"**作业名称:** {assignment_stats.assignment_name}")
        st.markdown(f"**学生总数:** {assignment_stats.total_students}")
        st.markdown(f"**提交人数:** {assignment_stats.submitted_count}")
        st.markdown(f"**平均分:** {assignment_stats.avg_score:.1f}")
        st.markdown(f"**最高分:** {assignment_stats.max_score:.1f}")
        st.markdown(f"**最低分:** {assignment_stats.min_score:.1f}")
        st.markdown(f"**及格率:** {assignment_stats.pass_rate:.1f}%")
    
    st.markdown("---")
    
    # Display top students
    st.markdown("### 学生成绩排行 (前10名)")
    sorted_students = sorted(students, key=lambda x: x.percentage, reverse=True)
    
    # Prepare data for display
    data = []
    for i, student in enumerate(sorted_students[:10], 1):
        data.append({
            "排名": i,
            "学号": student.student_id,
            "姓名": student.student_name,
            "总分": f"{student.total_score:.1f}/{student.max_score}",
            "百分比": f"{student.percentage:.1f}%",
            "等级": student.grade_level
        })
    
    import pandas as pd
    df = pd.DataFrame(data)
    st.dataframe(df, use_container_width=True)
    
    st.markdown("---")
    
    # Display question analysis if available
    if question_analysis:
        st.markdown("### 题目分析概览")
        # Prepare data for display
        question_data = []
        for question in question_analysis[:10]:  # Show first 10 questions
            question_data.append({
                "题目ID": question.question_id,
                "题型": question.question_type,
                "难度系数": f"{question.difficulty:.2f}",
                "正确率": f"{question.correct_rate:.1%}",
                "平均分": f"{question.avg_score:.1f}/{question.max_score}"
            })
        
        df_questions = pd.DataFrame(question_data)
        st.dataframe(df_questions, use_container_width=True)





def render_completed_records():
    """渲染已完成的批改记录"""
    st.markdown("## ✅ 已完成批改")
    st.markdown("这里显示已完成AI批改的作业记录，可以查看结果和可视化分析。")
    
    # 同步完成记录
    sync_completed_records()
    
    # 合并来自jobs的已完成记录
    all_completed = {}
    all_completed.update(st.session_state.completed_records)
    
    # 从jobs中获取已完成的记录
    if "jobs" in st.session_state and st.session_state.jobs:
        # Create a copy of the keys to avoid "dictionary changed size during iteration" error
        job_ids = list(st.session_state.jobs.keys())
        for job_id in job_ids:
            # Check if job_id still exists (in case it was deleted during iteration)
            if job_id not in st.session_state.jobs:
                continue
                
            # Skip mock jobs entirely
            if job_id.startswith("MOCK_JOB_"):
                continue
                
            task_info = st.session_state.jobs[job_id]
            
            # Check if this is a mock job
            is_mock = task_info.get("is_mock", False)
            
            if is_mock:
                continue
            
            try:
                result = requests.get(f"{st.session_state.backend}/ai_grading/grade_result/{job_id}", timeout=5)
                result.raise_for_status()
                status = result.json().get("status", "未知")
                
                if status == "completed" and job_id not in all_completed:
                    all_completed[job_id] = {
                        "task_name": task_info.get("name", "未知任务"),
                        "submitted_at": task_info.get("submitted_at", "未知时间"),
                        "completed_at": "刚刚",
                        "status": status
                    }
            except:
                continue
    
    # 添加mock数据作为已完成的批改记录
    if 'sample_data' in st.session_state and st.session_state.sample_data:
        assignment_stats = st.session_state.sample_data.get('assignment_stats')
        if assignment_stats:
            # Check if we already have a mock job entry
            mock_job_exists = any("MOCK_JOB" in job_id for job_id in all_completed.keys())
            
            if not mock_job_exists:
                # Add mock data as a completed job
                mock_job_id = "MOCK_JOB_001"
                submit_time = assignment_stats.create_time.strftime("%Y-%m-%d %H:%M:%S") if hasattr(assignment_stats.create_time, 'strftime') else "未知时间"
                all_completed[mock_job_id] = {
                    "task_name": assignment_stats.assignment_name,
                    "submitted_at": submit_time,
                    "completed_at": submit_time,
                    "status": "completed"
                }
    
    if not all_completed:
        st.info("暂无已完成的批改记录。")
        return
    
    # 显示已完成记录
    for job_id, record in all_completed.items():
        with st.container():
            st.markdown(f"""
            <div style="background: white; padding: 1.5rem; border-radius: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); margin: 1rem 0; border-left: 4px solid #10B981;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <h3 style="color: #1E3A8A; margin: 0 0 0.5rem 0;">✅ {record['task_name']}</h3>
                        <p style="color: #64748B; margin: 0; font-size: 0.9rem;">
                            <strong>提交时间:</strong> {record['submitted_at']} | 
                            <strong>完成时间:</strong> {record['completed_at']}
                        </p>
                    </div>
                    <div>
                        <span style="background: #D1FAE5; color: #065F46; padding: 0.25rem 0.75rem; border-radius: 20px; font-size: 0.8rem; font-weight: 600;">
                            已完成
                        </span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # 操作按钮
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                if st.button("📊 查看结果", key=f"view_{job_id}", use_container_width=True, type="primary"):
                    # For mock jobs, directly load the mock data into session state
                    if job_id.startswith("MOCK_JOB"):
                        # Load mock data directly into ai_grading_data so score_report.py can use it
                        st.session_state.ai_grading_data = st.session_state.sample_data
                        st.session_state.selected_job_id = None  # Don't set job ID for mock data
                    else:
                        st.session_state.selected_job_id = job_id
                    st.switch_page("pages/score_report.py")
            
            with col2:
                if st.button("📈 可视化分析", key=f"viz_{job_id}", use_container_width=True):
                    # For mock jobs, directly load the mock data into session state
                    if job_id.startswith("MOCK_JOB"):
                        # Load mock data directly into ai_grading_data so visualization.py can use it
                        st.session_state.ai_grading_data = st.session_state.sample_data
                        st.session_state.selected_job_id = None  # Don't set job ID for mock data
                    else:
                        st.session_state.selected_job_id = job_id
                    st.switch_page("pages/visualization.py")
            
            with col3:
                if st.button("📄 生成报告", key=f"report_{job_id}", use_container_width=True):
                    try:
                        # Import PDF generator
                        from frontend_utils.pdf_generator import generate_assignment_report
                        
                        # Get data for the report
                        if job_id.startswith("MOCK_JOB"):
                            # Use mock data
                            data = st.session_state.sample_data
                        else:
                            # Fetch data from backend
                            with st.spinner("正在获取数据..."):
                                ai_data = load_ai_grading_data(job_id)
                                if "error" not in ai_data:
                                    data = ai_data
                                else:
                                    st.error(f"获取数据失败: {ai_data['error']}")
                                    st.stop()
                        
                        students = data.get('student_scores', [])
                        assignment_stats = data.get('assignment_stats', None)
                        question_analysis = data.get('question_analysis', [])
                        
                        if assignment_stats and students:
                            with st.spinner("正在生成报告..."):
                                # Generate PDF report
                                pdf_path = generate_assignment_report(assignment_stats, students, question_analysis)
                                
                                # Provide download link
                                with open(pdf_path, "rb") as file:
                                    st.download_button(
                                        label="📥 下载PDF报告",
                                        data=file,
                                        file_name=f"{assignment_stats.assignment_name}_报告.pdf",
                                        mime="application/pdf",
                                        key=f"download_{job_id}"
                                    )
                                st.success("报告已生成！点击上方按钮下载。")
                        else:
                            st.warning("无法生成报告：缺少必要的数据。")
                    except Exception as e:
                        st.error(f"生成报告时出错: {str(e)}")
                        # Import PDF generator
                        from frontend_utils.pdf_generator import generate_assignment_report
                        
                        # Get data for the report
                        if job_id.startswith("MOCK_JOB"):
                            # Use mock data
                            data = st.session_state.sample_data
                        else:
                            # Fetch data from backend
                            with st.spinner("正在获取数据..."):
                                ai_data = load_ai_grading_data(job_id)
                                if "error" not in ai_data:
                                    data = ai_data
                                else:
                                    st.error(f"获取数据失败: {ai_data['error']}")
                                    st.stop()
                        
                        students = data.get('student_scores', [])
                        assignment_stats = data.get('assignment_stats', None)
                        question_analysis = data.get('question_analysis', [])
                        
                        if assignment_stats and students:
                            with st.spinner("正在生成报告..."):
                                # Generate PDF report
                                pdf_path = generate_assignment_report(assignment_stats, students, question_analysis)
                                
                                # Provide download link
                                with open(pdf_path, "rb") as file:
                                    st.download_button(
                                        label="📥 下载PDF报告",
                                        data=file,
                                        file_name=f"{assignment_stats.assignment_name}_报告.pdf",
                                        mime="application/pdf",
                                        key=f"download_{job_id}"
                                    )
                                st.success("报告已生成！点击上方按钮下载。")
                        else:
                            st.warning("无法生成报告：缺少必要的数据。")
                    except Exception as e:
                        st.error(f"生成报告时出错: {str(e)}")
            
            with col4:
                # Check if this is a mock job
                task_info = st.session_state.jobs.get(job_id, {}) if "jobs" in st.session_state else {}
                is_mock = task_info.get("is_mock", False) or job_id.startswith("MOCK_JOB")
                
                # Don't allow removal of mock jobs
                if not is_mock and st.button("🗑️ 移除", key=f"remove_{job_id}", use_container_width=True, type="secondary"):
                    # 从jobs中移除
                    if "jobs" in st.session_state and job_id in st.session_state.jobs:
                        del st.session_state.jobs[job_id]
                    # 从completed_records中移除
                    if job_id in st.session_state.completed_records:
                        del st.session_state.completed_records[job_id]
                    st.success("记录已移除！")
                    st.rerun()
                elif is_mock:
                    # For mock jobs, just show a disabled button or informative text
                    st.button(" Mock任务", key=f"remove_{job_id}", use_container_width=True, type="secondary", disabled=True)

def render_statistics_overview():
    """渲染统计概览"""
    st.markdown("## 📊 统计概览")
    
    # 计算统计数据
    completed_count = len(st.session_state.get('completed_records', {}))
    
    # 从jobs中计算已完成的任务
    if "jobs" in st.session_state and st.session_state.jobs:
        # Create a copy of the keys to avoid "dictionary changed size during iteration" error
        job_ids = list(st.session_state.jobs.keys())
        for job_id in job_ids:
            # Check if job_id still exists (in case it was deleted during iteration)
            if job_id not in st.session_state.jobs:
                continue
                
            # Skip mock jobs entirely
            if job_id.startswith("MOCK_JOB_"):
                continue
                
            task_info = st.session_state.jobs[job_id]
            
            # Check if this is a mock job
            is_mock = task_info.get("is_mock", False)
            
            if is_mock:
                continue
            
            try:
                result = requests.get(f"{st.session_state.backend}/ai_grading/grade_result/{job_id}", timeout=5)
                result.raise_for_status()
                status = result.json().get("status", "未知")
                if status == "completed":
                    completed_count += 1
            except:
                continue
    
    # 添加mock数据到统计中
    if 'sample_data' in st.session_state and st.session_state.sample_data:
        assignment_stats = st.session_state.sample_data.get('assignment_stats')
        if assignment_stats:
            completed_count += 1
    
    total_records = completed_count
    
    # 显示统计卡片
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        <div style="text-align: center; padding: 2rem; background: white; border-radius: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); border-top: 4px solid #1E3A8A;">
            <h1 style="color: #1E3A8A; margin: 0; font-size: 3rem;">{total_records}</h1>
            <p style="margin: 0.5rem 0 0 0; color: #64748B; font-weight: 600;">总记录数</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div style="text-align: center; padding: 2rem; background: white; border-radius: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); border-top: 4px solid #10B981;">
            <h1 style="color: #10B981; margin: 0; font-size: 3rem;">{completed_count}</h1>
            <p style="margin: 0.5rem 0 0 0; color: #64748B; font-weight: 600;">已完成</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        completion_rate = 100.0 if total_records > 0 else 0
        st.markdown(f"""
        <div style="text-align: center; padding: 2rem; background: white; border-radius: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); border-top: 4px solid #8B5CF6;">
            <h1 style="color: #8B5CF6; margin: 0; font-size: 3rem;">{completion_rate:.1f}%</h1>
            <p style="margin: 0.5rem 0 0 0; color: #64748B; font-weight: 600;">完成率</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # 最近活动
    st.markdown("### 📅 最近活动")
    st.info("暂无最近活动记录。")

def main():
    """主函数"""
    init_storage_state()
    
    render_header()
    st.markdown("---")
    
    render_tabs()
    
    # 在每个页面都调用这个函数
    inject_pollers_for_active_jobs()

if __name__ == "__main__":
    main()
