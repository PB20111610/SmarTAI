# utils.py
import streamlit as st
import streamlit.components.v1 as components
import json # 引入 json 库用于将 Python 列表转换为 JS 数组
import requests

def load_custom_css(file_path=None):
    """
    从指定路径加载CSS文件并应用到Streamlit应用中。
    自动处理相对路径问题。
    """
    import os
    
    if file_path is None:
        # 获取当前文件的目录
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # 构建CSS文件的绝对路径
        file_path = os.path.join(current_dir, "static", "main.css")
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        st.error(f"CSS文件未找到: {file_path}")
    except Exception as e:
        st.error(f"加载CSS文件时出错: {str(e)}")

def initialize_session_state():
    """
    在每个页面顶部运行的辅助函数，用于初始化 session_state。
    如果某个键不存在，就为其设置一个初始值。
    """
    if "jobs" not in st.session_state:
        st.session_state.jobs = {}
    
    # --- 关键改动在这里 ---
    # 如果 'backend' 这个键不存在于 session_state 中，就设置它的初始/固定值
    if "backend" not in st.session_state:
        # 在这里硬编码你的后端地址
        st.session_state.backend = "http://localhost:8000" 
        
    if 'prob_changed' not in st.session_state:
        st.session_state.prob_changed = False

    if 'ans_changed' not in st.session_state:
        st.session_state.ans_changed = False
        
def update_prob():
    if st.session_state.get('prob_changed', False):
        st.info("检测到题目数据已修改，正在更新存储到后端...") # 友好提示
        try:
            requests.post(
                f"{st.session_state.backend}/human_edit/problems",
                json=st.session_state.prob_data
            )
            
            print("数据已成功保存到后端！") # 在终端打印日志
            st.toast("更改已成功保存！", icon="✅")

            # 保存成功后，重置标志位
            st.session_state.prob_changed = False
        except Exception as e:
            st.error(f"保存失败，错误信息: {e}")
            print(f"Error saving to DB: {e}") # 在终端打印错误

def update_ans():
    if st.session_state.get('ans_changed', False):
        st.info("检测到学生作答数据已修改，正在更新存储到后端...") # 友好提示
        try:
            requests.post(
                f"{st.session_state.backend}/human_edit/stu_ans",
                json=st.session_state.processed_data
            )
            
            print("数据已成功保存到后端！") # 在终端打印日志
            st.toast("更改已成功保存！", icon="✅")

            # 保存成功后，重置标志位
            st.session_state.prob_changed = False
        except Exception as e:
            st.error(f"保存失败，错误信息: {e}")
            print(f"Error saving to DB: {e}") # 在终端打印错误

def get_master_poller_html(jobs_json: str, backend_url: str) -> str:
    """
    生成一个“主”轮询脚本。
    这个脚本接收一个包含所有任务详细信息的 JSON 对象，
    并在内部为每个 job_id 启动轮询。
    """
    be = backend_url.rstrip("/")
    # jobs_json 现在是一个字典的JSON字符串，例如：
    # '{"job1":{"name":"file1.pdf", "submitted_at":"..."}, "job2":{...}}'
    return f"""
    <script>
    (function() {{
        const backend = '{be}';
        let jobsData; // <-- 变量名修改，以反映其为数据对象

        try {{
            jobsData = JSON.parse('{jobs_json}');
        }} catch (e) {{
            console.error("无法解析任务数据对象:", e);
            jobsData = {{}};
        }}

        // 获取所有待轮询的任务ID (即对象的键)
        const jobIds = Object.keys(jobsData);

        if (jobIds.length === 0) {{
            return;
        }}

        // 定义一个为单个任务启动轮询的函数
        // <-- 接收 job_id 和对应的任务详情对象
        const startPollingForJob = (jobId, taskDetails) => {{
            const completedKey = `job-completed-${{jobId}}`;

            if (sessionStorage.getItem(completedKey)) {{
                return;
            }}

            const intervalId = setInterval(async () => {{
                try {{
                    // 轮询的URL依然只使用 job_id
                    const resp = await fetch(backend + '/ai_grading/grade_result/' + jobId);
                    if (!resp.ok) return;

                    const data = await resp.json();
                    if (data && data.status === 'completed') {{
                        clearInterval(intervalId);
                        if (!sessionStorage.getItem(completedKey)) {{
                            // --- 核心修改：生成用户友好的弹窗消息 ---
                            const taskName = taskDetails.name || "未命名任务";
                            const submittedAt = taskDetails.submitted_at || "未知时间";
                            alert(`您于 [${{submittedAt}}] 提交的任务\\n"${{taskName}}"\\n已成功完成！`);
                            // ------------------------------------
                            sessionStorage.setItem(completedKey, 'true');
                        }}
                    }}
                }} catch (err) {{
                    // 静默处理错误
                }}
            }}, 3000);
        }};

        // 遍历所有任务ID，为每一个启动轮询，并传入其详细信息
        jobIds.forEach(jobId => {{
            startPollingForJob(jobId, jobsData[jobId]);
        }});

    }})();
    </script>
    """

def inject_pollers_for_active_jobs():
    """
    【核心函数优化版】将所有活动任务的ID打包，一次性注入一个主轮询器。
    """
    if "jobs" not in st.session_state:
        st.session_state.jobs = {}
    if "backend" not in st.session_state:
        st.session_state.backend = "http://localhost:8000"

    if not st.session_state.jobs:
        return

    # 将 Python 的 job_id 列表转换为 JSON 格式的字符串
    jobs_json_string = json.dumps(st.session_state.jobs)

    # 获取包含所有轮询逻辑的单个主脚本
    master_js_code = get_master_poller_html(jobs_json_string, st.session_state.backend)

    # 全局只调用这一次 components.html！
    components.html(master_js_code, height=0)