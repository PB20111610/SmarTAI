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
    st.warning("当前没有批改任务记录。")
    st.page_link("pages/stu_preview.py", label="返回学生作业总览", icon="📖")
    st.stop()

# --- 页面内容 ---
st.title("📊 AI批改结果")

# Get job IDs
job_ids = list(st.session_state.jobs.keys())
if not job_ids:
    st.info("没有找到批改任务。")
else:
    # If we came from the history page with a selected job, use that
    # Otherwise, let the user select a job
    if selected_job_id and selected_job_id in st.session_state.jobs:
        selected_job = selected_job_id
        # Clear the selected job ID from session state
        del st.session_state.selected_job_id
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
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📊 查看评分报告", use_container_width=True):
                # Set the selected job ID in session state for the score report page
                st.session_state.selected_job_id = selected_job
                st.switch_page("pages/score_report.py")
        
        with col2:
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
            
            if status == "completed":
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
                            data.append({
                                "题目ID": correction["q_id"],
                                "题目类型": correction["type"],
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
                        data.append({
                            "题目ID": correction["q_id"],
                            "题目类型": correction["type"],
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