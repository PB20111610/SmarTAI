# pages/stu_details.py

import streamlit as st
from streamlit_scroll_to_top import scroll_to_here
from utils import *

# --- 页面基础设置 (建议添加) ---
st.set_page_config(
    page_title="学生作业详情 - 智能作业核查系统",
    layout="wide",
    page_icon="📖"
)

initialize_session_state()

# 在每个页面的顶部调用这个函数
load_custom_css()

st.page_link("main.py", label="home", icon="🏠")

st.page_link("pages/problems.py", label="返回题目识别概览", icon="📝")

# --- 安全检查 ---
# 检查必要的数据是否已加载
if 'prob_data' not in st.session_state or not st.session_state.get('prob_data'):
    st.warning("请先在“作业题目上传”页面上传并作业题目文件。")
    st.page_link("pages/prob_upload.py", label="返回上传页面", icon="📤")
    st.stop()
if 'processed_data' not in st.session_state or not st.session_state.get('processed_data'):
    st.warning("请先在“作业上传”页面上传并处理文件。")
    st.page_link("pages/hw_upload.py", label="返回上传页面", icon="📤")
    st.stop()

# 检查是否有学生被选中，防止用户直接访问此页面
if 'selected_student_id' not in st.session_state or not st.session_state.get('selected_student_id'):
    st.warning("请先从“学生作业总览”页面选择一个学生。")
    st.page_link("pages/stu_preview.py", label="返回总览页面", icon="📖")
    st.stop()


# --- 滚动逻辑 ---
# 每次进入详情页时，自动滚动到顶部
scroll_to_here(50, key='top')
scroll_to_here(0, key='top_fix')


# --- 侧边栏导航 (与总览页保持一致) ---
with st.sidebar:
    st.header("导航")
    
    # st.page_link("pages/problems.py", label="题目识别概览", icon="📝")
    st.page_link("pages/stu_preview.py", label="学生作业总览", icon="📖")

    with st.expander("按学生查看", expanded=True):
        student_list = sorted(list(st.session_state.processed_data.get('students', {}).keys()))
        
        # 获取当前正在查看的学生ID
        current_sid = st.session_state.get('selected_student_id')

        if not student_list:
            st.caption("暂无学生数据")
        else:
            # 定义回调函数，用于切换查看不同的学生
            def select_student(sid):
                st.session_state['selected_student_id'] = sid
                # 由于已经在详情页，切换学生只需 rerun 即可，无需切换页面
                # st.rerun()

            for sid in student_list:
                # 判断当前按钮是否为正在查看的学生
                is_selected = (sid == current_sid)
                st.button(
                    sid, 
                    key=f"btn_student_{sid}", 
                    on_click=select_student,
                    args=(sid,),
                    disabled=is_selected, # 禁用当前已选中的学生按钮
                    width='stretch',
                    # type='primary'
                )


# --- 主页面内容：学生详情视图 ---

def render_student_view(student_id):
    st.header(f"🧑‍🎓 学生作业详情: {student_id}")
    
    student_data = st.session_state.processed_data.get('students', {}).get(student_id, {})
    all_questions = {q['id']: q for q in st.session_state.prob_data.get('questions', [])}
    answers = student_data.get('answers', [])
    
    if not answers:
        st.warning("未找到该学生的任何答案提交记录。")
        return
        
    for ans in answers:
        q_id = ans.get('question_id')
        question_info = all_questions.get(q_id)
        if not question_info: continue
        
        st.markdown(f"#### 题目 {question_info.get('number', '')}:")
        stem_text = question_info.get('stem', '').strip()
        if stem_text.startswith('$') and stem_text.endswith('$'):
            st.latex(stem_text.strip('$'))
        else:
            st.markdown(stem_text)
            
        if ans.get('flags'):
            for flag in ans['flags']:
                st.error(f"🚩 **需人工处理**: {flag}")
                
        q_type = question_info.get('type')
        content = ans.get('content')
        
        st.markdown("**学生答案:**")
        if q_type == "编程题" and isinstance(content, dict):
            if content.keys():
                file_to_show = st.selectbox("选择代码文件", options=list(content.keys()), key=f"file_{student_id}_{q_id}")
                if file_to_show:
                    st.code(content[file_to_show], language="python")
            else:
                st.info("该学生未提交此编程题的文件。")
        else:
            try:
                content_str = str(content).strip()
                if content_str.startswith('$') and content_str.endswith('$'):
                    st.latex(content_str.strip('$'))
                else:
                    st.markdown(content_str, unsafe_allow_html=True)
            except Exception:
                st.text(str(content))
        st.divider()

# 获取当前选定的学生ID并渲染其视图
selected_student_id = st.session_state.get('selected_student_id')
render_student_view(selected_student_id)

# --- 新增：右下角跳转链接 ---
def start_ai_grading_and_navigate():
    """
    这个函数做了两件事：
    1. 在 session_state 中设置一个“一次性触发”的标志。
    2. 命令 Streamlit 跳转到任务轮询页面。
    """
    st.session_state.trigger_ai_grading = True  # 使用与目标页面匹配的标志
    # st.switch_page("pages/wait_ai_grade.py")   # 跳转到你的目标页面

# ----------------------------------------------------
# 添加一个分隔符，使其与主内容分开
st.divider()

# 使用列布局将按钮推到右侧 (这部分和你的代码一样)
col_spacer, col_button = st.columns([4, 1])

with col_button:
    # 2. 创建一个按钮，并告诉它在被点击时调用上面的函数
    if st.button(
        "开启AI批改", 
        on_click=start_ai_grading_and_navigate, 
        width='stretch' # 让按钮填满列宽，视觉效果更好
    ):
        st.switch_page("pages/wait_ai_grade.py")   # 跳转到你的目标页面

inject_pollers_for_active_jobs()