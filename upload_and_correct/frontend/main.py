# main_temp.py (模拟主入口，仅供您独立开发时使用)

import streamlit as st
from utils import *

st.set_page_config(
    page_title="开发测试入口",
    layout="centered"
)

initialize_session_state()

st.title("项目开发 - 模拟主入口")

st.info("此页面用于模拟最终应用的登录流程。")
st.warning("它会自动设置'已登录'状态，并准备跳转到您负责的模块。")

# --- 模拟最终 main.py 会做的事 ---

# 1. 模拟登录成功，为 session state 注入必要的状态
#    您的其他页面依赖 st.session_state.logged_in，所以我们在这里设置它
st.session_state.logged_in = True

# 2. 如果您的页面还需要其他前置数据，也可以在这里模拟
#    例如: st.session_state.user_info = {"name": "developer", "role": "admin"}


st.markdown("---")


# --- 提供跳转按钮 ---
# 这个按钮是您进入您负责模块的入口
# 它会跳转到您模块的第一个页面
if st.button("▶️ 开始开发/测试我的模块 (作业上传)", type="primary"):
    st.switch_page("pages/prob_upload.py")

inject_pollers_for_active_jobs()