import streamlit as st
import requests
from utils import *

# --- 页面基础设置 (建议添加) ---
st.set_page_config(
    page_title="批改任务记录",
    layout="wide",
    page_icon="📝"
)

initialize_session_state()

# 在每个页面的顶部调用这个函数
load_custom_css()

st.page_link("main.py", label="home", icon="🏠")

# st.write("从当前会话记录中读取 job_id 并查询状态。")


import streamlit as st
import requests

# 检查 session state 中是否有任务记录
# (st.session_state.jobs 现在是一个字典)
if "jobs" not in st.session_state or not st.session_state.jobs:
    st.info("当前会话没有任务记录。请先到“开始任务”页面提交任务并等待完成。")
else:
    st.subheader("任务状态列表")

    # --- 核心修改：迭代字典的键和值 ---
    # 我们使用 .items() 来同时获取 job_id 和包含任务详情的 task_info 字典
    # 使用 list() 来创建一个副本，这样在循环中删除字典项时不会出错
    for job_id, task_info in list(st.session_state.jobs.items()):
        
        # 从 task_info 字典中安全地获取任务名和提交时间
        task_name = task_info.get("name", "未知任务")
        submission_time = task_info.get("submitted_at", "未知时间")
        
        status = "查询中..." # 默认状态
        try:
            # 后端请求依然使用唯一的 job_id
            result = requests.get(f"{st.session_state.backend}/ai_grading/{job_id}", timeout=10)
            result.raise_for_status()
            status = result.json().get("status", "未知")
        except Exception as e:
            # 简化了错误信息的显示
            status = "查询失败"
            print(f"查询任务 {job_id} ({task_name}) 状态失败: {e}") # 在后台打印详细错误

        # --- 核心修改：更新显示布局 ---
        # 调整列的比例以适应新内容
        cols = st.columns([4, 3, 2, 2])
        
        # 第1列：显示任务名称
        cols[0].write(f"**任务名称**：`{task_name}`")
        
        # 第2列：显示提交时间
        cols[1].write(f"**提交时间**：{submission_time}")
        
        # 第3列：显示状态
        cols[2].write(f"**状态**：{status}")
        
        # 第4列：显示操作按钮（如果任务已完成）
        if status == "completed":
            # key 依然使用 job_id 来确保唯一性
            if cols[3].button("从列表中移除", key=f"rm_{job_id}"):
                # --- 核心修改：从字典中删除条目 ---
                del st.session_state.jobs[job_id]
                # 刷新页面以立即看到移除效果
                st.rerun()
        else:
            # 如果任务未完成，则第四列留空
            cols[3].write("") 
        
        st.divider() # 在每个任务条目后添加分隔线


    st.button("手动刷新状态（点击会重新加载页面）")

# 在每个页面都调用这个函数！
inject_pollers_for_active_jobs()