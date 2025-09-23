import streamlit as st
import requests
import pandas as pd
from utils import *

# --- 页面基础设置 ---
st.set_page_config(
    page_title="AI批改结果 - 智能作业核查系统",
    layout="wide",
    page_icon="📊"
)

initialize_session_state()

# 在每个页面的顶部调用这个函数
load_custom_css()

st.page_link("main.py", label="home", icon="🏠")

# --- 安全检查 ---
# Check if we're coming from the history page with a selected job
selected_job_id = st.session_state.get("selected_job_id", None)

# Check if we have job records
if "jobs" not in st.session_state or not st.session_state.jobs:
    # Check if we have a current job from wait_ai_grade page
    if "current_job_id" in st.session_state:
        # Create a temporary job record
        temp_job_id = st.session_state.current_job_id
        st.session_state.jobs = {temp_job_id: {"name": "最近批改任务", "submitted_at": "刚刚"}}
        selected_job_id = temp_job_id
        # Clean up the temporary job ID
        del st.session_state.current_job_id
    else:
        st.warning("当前没有批改任务记录。")
        st.page_link("pages/stu_preview.py", label="返回学生作业总览", icon="📖")
        st.stop()

# --- 页面内容 ---
st.title("📊 AI批改结果")

# Add debug button
if st.button("调试：检查所有任务"):
    from frontend_utils.data_loader import check_all_jobs
    all_jobs = check_all_jobs()
    st.write("所有任务状态:", all_jobs)

# 映射题目类型：从内部类型到中文显示名称
type_display_mapping = {
    "concept": "概念题",
    "calculation": "计算题", 
    "proof": "证明题",
    "programming": "编程题"
}

# Get job IDs
job_ids = list(st.session_state.jobs.keys())
if not job_ids:
    st.info("没有找到批改任务。")
else:
    # If we came from the history page with a selected job, use that
    # Otherwise, let the user select a job
    if selected_job_id and selected_job_id in st.session_state.jobs:
        selected_job = selected_job_id
        # Don't clear the selected job ID from session state, keep it for other pages
        # del st.session_state.selected_job_id
    elif "current_job_id" in st.session_state and st.session_state.current_job_id in st.session_state.jobs:
        selected_job = st.session_state.current_job_id
        # Clean up the temporary job ID
        del st.session_state.current_job_id
    else:
        selected_job = st.selectbox(
            "选择一个批改任务",
            job_ids,
            format_func=lambda x: st.session_state.jobs[x].get("name", x)
        )
    
    if selected_job:
        # 获取任务详情
        task_info = st.session_state.jobs[selected_job]
        st.subheader(f"任务: {task_info.get('name', '未知任务')}")
        st.write(f"提交时间: {task_info.get('submitted_at', '未知时间')}")
        
        # 添加按钮导航到评分报告和可视化页面
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("🏠 返回首页", use_container_width=True):
                st.switch_page("main.py")
        
        with col2:
            if st.button("📊 查看评分报告", use_container_width=True):
                # Set the selected job ID in session state for the score report page
                st.session_state.selected_job_id = selected_job
                st.switch_page("pages/score_report.py")
        
        with col3:
            if st.button("📈 查看可视化分析", use_container_width=True):
                # Set the selected job ID in session state for the visualization page
                st.session_state.selected_job_id = selected_job
                st.switch_page("pages/visualization.py")
        
        st.markdown("---")
        
        # 获取批改结果
        try:
            response = requests.get(
                f"{st.session_state.backend}/ai_grading/grade_result/{selected_job}",
                timeout=10
            )
            response.raise_for_status()
            result = response.json()
            
            status = result.get("status", "未知")
            st.write(f"状态: {status}")
            
            # Key fix: Check if we have data even if status is not explicitly "completed"
            has_data = "results" in result or "corrections" in result
            
            if status == "completed" or has_data:
                # 显示结果
                if "results" in result:  # Batch grading results
                    all_results = result["results"]
                    st.subheader("所有学生批改结果")
                    
                    for student_result in all_results:
                        student_id = student_result["student_id"]
                        corrections = student_result["corrections"]
                        
                        st.markdown(f"### 学生: {student_id}")
                        
                        # 准备数据用于显示
                        data = []
                        total_score = 0
                        total_max_score = 0
                        
                        for correction in corrections:
                            # 直接使用返回的类型，如果已经是中文则直接使用，否则进行映射
                            question_type = correction["type"]
                            if question_type in type_display_mapping:
                                display_type = type_display_mapping[question_type]
                            elif question_type in type_display_mapping.values():
                                display_type = question_type
                            else:
                                display_type = "概念题"  # 默认类型
                            
                            data.append({
                                "题目ID": correction["q_id"],
                                "题目类型": display_type,  # 使用中文显示类型
                                "得分": f"{correction['score']:.1f}",
                                "满分": f"{correction['max_score']:.1f}",
                                "置信度": f"{correction['confidence']:.2f}",
                                "评语": correction["comment"]
                            })
                            total_score += correction["score"]
                            total_max_score += correction["max_score"]
                        
                        # 显示该学生的批改结果表格
                        df = pd.DataFrame(data)
                        st.dataframe(df, use_container_width=True)
                        
                        # 显示总分
                        st.write(f"**总分: {total_score:.1f}/{total_max_score:.1f}**")
                        st.divider()
                        
                elif "corrections" in result:  # Single student grading results
                    corrections = result["corrections"]
                    st.subheader(f"学生 {result.get('student_id', '未知学生')} 的批改结果")
                    
                    # 准备数据用于显示
                    data = []
                    total_score = 0
                    total_max_score = 0
                    
                    for correction in corrections:
                        # 直接使用返回的类型，如果已经是中文则直接使用，否则进行映射
                        question_type = correction["type"]
                        if question_type in type_display_mapping:
                            display_type = type_display_mapping[question_type]
                        elif question_type in type_display_mapping.values():
                            display_type = question_type
                        else:
                            display_type = "概念题"  # 默认类型
                        
                        data.append({
                            "题目ID": correction["q_id"],
                            "题目类型": display_type,  # 使用中文显示类型
                            "得分": f"{correction['score']:.1f}",
                            "满分": f"{correction['max_score']:.1f}",
                            "置信度": f"{correction['confidence']:.2f}",
                            "评语": correction["comment"]
                        })
                        total_score += correction["score"]
                        total_max_score += correction["max_score"]
                    
                    # 显示批改结果表格
                    df = pd.DataFrame(data)
                    st.dataframe(df, use_container_width=True)
                    
                    # 显示总分
                    st.write(f"**总分: {total_score:.1f}/{total_max_score:.1f}**")
                else:
                    st.warning("批改结果中没有找到学生数据。")
            elif status == "error":
                st.error(f"批改过程中出现错误: {result.get('message', '未知错误')}")
            elif status == "pending":
                st.info("批改任务正在进行中，请稍候...")
            else:
                st.warning(f"未知状态: {status}")
                
        except requests.exceptions.RequestException as e:
            st.error(f"获取批改结果失败: {e}")
        except Exception as e:
            st.error(f"处理批改结果时出现错误: {e}")

inject_pollers_for_active_jobs()

# Add a link back to the history page
st.page_link("pages/history.py", label="返回任务记录", icon="⬅️")