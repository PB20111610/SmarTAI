"""
SmarTAI项目 - 主应用入口文件

智能评估平台的主界面，提供导航和核心功能入口
"""

import streamlit as st
import sys
import os
from datetime import datetime
from typing import Dict, Any

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import from utils.py (the file, not the folder)
from utils import *
# Import from frontend_utils (the folder we renamed)
from frontend_utils.data_loader import load_ai_grading_data, StudentScore, QuestionAnalysis, AssignmentStats
from frontend_utils.chart_components import create_score_distribution_chart, create_grade_pie_chart

# 页面配置
st.set_page_config(
    page_title="SmarTAI - 智能评估平台",
    page_icon="🎓",
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
        .hero-section {
            text-align: center;
            padding: 3rem 0;
            background: linear-gradient(135deg, #1E3A8A 0%, #3B82F6 100%);
            color: white;
            border-radius: 15px;
            margin-bottom: 2rem;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        .feature-card {
            background: white;
            padding: 2rem;
            border-radius: 15px;
            box-shadow: 0 8px 25px rgba(0,0,0,0.1);
            text-align: center;
            transition: all 0.3s ease;
            border-top: 4px solid #1E3A8A;
            height: 100%;
        }
        .feature-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 15px 35px rgba(0,0,0,0.15);
        }
        .feature-icon {
            font-size: 3rem;
            margin-bottom: 1rem;
        }
        .feature-title {
            font-size: 1.5rem;
            font-weight: 700;
            color: #1E3A8A;
            margin-bottom: 1rem;
        }
        .feature-description {
            color: #64748B;
            line-height: 1.6;
            margin-bottom: 1.5rem;
        }
        .stats-card {
            background: white;
            padding: 1.5rem;
            border-radius: 10px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            text-align: center;
            border-left: 4px solid #10B981;
        }
        .stats-number {
            font-size: 2.5rem;
            font-weight: 700;
            color: #1E3A8A;
            margin-bottom: 0.5rem;
        }
        .stats-label {
            color: #64748B;
            font-size: 0.875rem;
            text-transform: uppercase;
            font-weight: 600;
        }
        .quick-access {
            background: #F8FAFC;
            padding: 2rem;
            border-radius: 15px;
            margin: 2rem 0;
        }
        </style>
        """, unsafe_allow_html=True)

def init_session_state():
    """初始化会话状态"""
    # Initialize session state from utils.py
    initialize_session_state()
    
    # Set logged in state
    st.session_state.logged_in = True
    
    # Initialize sample data or AI grading data
    if 'sample_data' not in st.session_state:
        with st.spinner("初始化系统数据..."):
            # Try to load AI grading data if a job is selected
            if 'selected_job_id' in st.session_state:
                ai_data = load_ai_grading_data(st.session_state.selected_job_id)
                if "error" not in ai_data:
                    st.session_state.sample_data = ai_data
                else:
                    # Fallback to default data if AI data loading fails
                    st.session_state.sample_data = create_default_data()
            else:
                # Use default data when no job is selected
                st.session_state.sample_data = create_default_data()
    
    if 'user_info' not in st.session_state:
        st.session_state.user_info = {
            'name': '张老师',
            'role': '任课教师',
            'department': '计算机科学与技术学院'
        }

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
    
    # Create default question analysis
    questions = [
        QuestionAnalysis(
            question_id="Q1",
            question_type="concept",
            topic="数据结构基础",
            difficulty=0.3,
            correct_rate=0.85,
            avg_score=8.5,
            max_score=10
        ),
        QuestionAnalysis(
            question_id="Q2",
            question_type="calculation",
            topic="算法复杂度",
            difficulty=0.7,
            correct_rate=0.65,
            avg_score=6.5,
            max_score=10
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
        "question_analysis": questions,
        "assignment_stats": assignment_stats
    }

def render_hero_section():
    """渲染主题部分"""
    st.markdown("""
    <div class="hero-section">
        <h1 style="font-size: 3rem; margin-bottom: 1rem; font-weight: 700;">🎓 SmarTAI</h1>
        <h2 style="font-size: 1.5rem; margin-bottom: 1rem; opacity: 0.9;">智能评估平台</h2>
        <p style="font-size: 1.125rem; opacity: 0.8; max-width: 600px; margin: 0 auto;">
            基于人工智能的理工科教育评估系统<br>
            提供智能评分、深度分析和可视化报告
        </p>
    </div>
    """, unsafe_allow_html=True)

def render_user_welcome():
    """渲染用户欢迎信息"""
    user_info = st.session_state.user_info
    col1, col2, col3, col4 = st.columns([2, 2, 1, 1])
    
    with col1:
        # 显示登录用户信息
        username = st.session_state.get('username', user_info['name'])
        st.markdown(f"""
        ### 👋 欢迎回来，{username}！
        **{user_info['role']}** | {user_info['department']}
        """)
    
    with col2:
        current_time = datetime.now()
        st.markdown(f"""
        ### 📅 今日信息
        **日期:** {current_time.strftime('%Y年%m月%d日')}<br>
        **时间:** {current_time.strftime('%H:%M')}
        """, unsafe_allow_html=True)
    
    with col3:
        if st.button("🔄 刷新数据", use_container_width=True):
            # Refresh data based on selected job or default data
            if 'selected_job_id' in st.session_state:
                ai_data = load_ai_grading_data(st.session_state.selected_job_id)
                if "error" not in ai_data:
                    st.session_state.sample_data = ai_data
                else:
                    st.error(f"刷新数据失败: {ai_data['error']}")
            else:
                st.session_state.sample_data = create_default_data()
            st.success("数据已刷新！")
            st.rerun()
    
    with col4:
        if st.button("🚪 退出登录", use_container_width=True, type="secondary"):
            # 清除登录状态
            st.session_state.logged_in = False
            st.session_state.username = ""
            st.success("已退出登录")
            st.switch_page("pages/login.py")

def render_statistics_overview():
    """渲染统计概览"""
    st.markdown("## 📊 今日概览")
    
    # 获取统计数据
    data = st.session_state.sample_data
    students = data['student_scores']
    assignment_stats = data['assignment_stats']
    
    # 计算统计指标
    total_students = len(students)
    avg_score = sum(s.percentage for s in students) / len(students) if students else 0
    pass_rate = len([s for s in students if s.percentage >= 60]) / len(students) * 100 if students else 0
    need_review = len([s for s in students if s.need_review])
    
    # 显示统计卡片
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="stats-card">
            <div class="stats-number">{total_students}</div>
            <div class="stats-label">学生总数</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="stats-card">
            <div class="stats-number">{avg_score:.1f}%</div>
            <div class="stats-label">平均成绩</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="stats-card">
            <div class="stats-number">{pass_rate:.1f}%</div>
            <div class="stats-label">及格率</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="stats-card">
            <div class="stats-number">{need_review}</div>
            <div class="stats-label">待复核</div>
        </div>
        """, unsafe_allow_html=True)

def render_feature_cards():
    """渲染功能特性卡片"""
    st.markdown("## 🚀 核心功能")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">📊</div>
            <div class="feature-title">评分报告</div>
            <div class="feature-description">
                查看学生作业详细评分结果，支持人工修改和批量操作。
                提供置信度分析和复核建议。
            </div>
        """, unsafe_allow_html=True)
        
        if st.button("📊 查看评分报告", use_container_width=True, type="primary"):
            # Clear any existing selected job ID to show sample data by default
            if 'selected_job_id' in st.session_state:
                del st.session_state.selected_job_id
            st.switch_page("pages/score_report.py")

        st.markdown("</div>", unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">📈</div>
            <div class="feature-title">可视化分析</div>
            <div class="feature-description">
                深度分析学生表现和题目质量，生成交互式图表和统计报告。
                支持多维度数据分析。
            </div>
        """, unsafe_allow_html=True)
        
        if st.button("📈 查看可视化分析", use_container_width=True, type="primary"):
            # Clear any existing selected job ID to show sample data by default
            if 'selected_job_id' in st.session_state:
                del st.session_state.selected_job_id
            st.switch_page("pages/visualization.py")

        st.markdown("</div>", unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">📚</div>
            <div class="feature-title">历史记录</div>
            <div class="feature-description">
                查看历史批改记录，支持暂存功能。可以预览、编辑暂存记录，
                查看已完成批改的详细结果和可视化分析。
            </div>
        """, unsafe_allow_html=True)
        
        if st.button("📚 查看历史记录", use_container_width=True, type="primary"):
            st.switch_page("pages/history_enhanced.py")

        st.markdown("</div>", unsafe_allow_html=True)

def render_upload_section():
    """渲染上传功能区域"""
    st.markdown("## 📤 作业上传")
    
    st.markdown("""
    <div style="background: white; padding: 2rem; border-radius: 15px; box-shadow: 0 8px 25px rgba(0,0,0,0.1); border-top: 4px solid #1E3A8A;">
        <h3 style="color: #1E3A8A; margin-top: 0;">开始新的作业批改流程</h3>
        <p>上传题目和学生作业文件，启动AI智能批改流程。</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📝 第一步：上传题目文件")
        st.markdown("上传包含题目的PDF或Word文档")
        if st.button("📁 上传题目文件", use_container_width=True, type="primary"):
            st.switch_page("pages/prob_upload.py")

    with col2:
        st.markdown("### 📄 第二步：上传学生作业")
        st.markdown("上传学生提交的作业文件")
        if st.button("📁 上传学生作业", use_container_width=True, type="primary"):
            st.switch_page("pages/hw_upload.py")

def render_quick_preview():
    """渲染快速预览"""
    st.markdown("## 👀 快速预览")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📊 成绩分布")
        try:
            students = st.session_state.sample_data['student_scores']
            fig = create_score_distribution_chart(students)
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"生成图表时出错: {str(e)}")
    
    with col2:
        st.markdown("### 🏆 成绩等级")
        try:
            students = st.session_state.sample_data['student_scores']
            fig = create_grade_pie_chart(students)
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"生成图表时出错: {str(e)}")

def render_quick_actions():
    """渲染快速操作"""
    st.markdown("""
    <div class="quick-access">
        <h3 style="color: #1E3A8A; margin-bottom: 1.5rem;">⚡ 快速操作</h3>
    """, unsafe_allow_html=True)
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        if st.button("📋 最新作业", use_container_width=True):
            st.info("🔄 跳转到最新作业评分...")
    
    with col2:
        if st.button("⚠️ 待复核列表", use_container_width=True):
            st.info("📝 显示需要复核的作业...")
    
    with col3:
        if st.button("📈 生成报告", use_container_width=True):
            with st.spinner("生成综合分析报告中..."):
                import time
                time.sleep(2)
            st.success("✅ 综合分析报告已生成！")
    
    with col4:
        if st.button("📚 知识库管理", use_container_width=True):
            st.switch_page("pages/knowledge_base.py")
    
    with col5:
        if st.button("⚙️ 系统设置", use_container_width=True):
            st.info("🔧 打开系统设置界面...")
    
    st.markdown("</div>", unsafe_allow_html=True)

def render_recent_activities():
    """渲染最近活动"""
    st.markdown("## 🕐 最近活动")
    
    activities = [
        {
            "time": "2小时前",
            "action": "批量导出PDF报告",
            "details": "导出了45名学生的评分报告",
            "status": "完成"
        },
        {
            "time": "5小时前",
            "action": "复核低置信度答案",
            "details": "复核了8道置信度低于70%的题目",
            "status": "完成"
        },
        {
            "time": "1天前",
            "action": "生成可视化分析",
            "details": "为数据结构课程生成了综合分析报告",
            "status": "完成"
        },
        {
            "time": "2天前",
            "action": "上传新作业",
            "details": "上传了期中考试试卷，等待AI评分",
            "status": "处理中"
        }
    ]
    
    for activity in activities:
        status_color = "#10B981" if activity["status"] == "完成" else "#F59E0B"
        st.markdown(f"""
        <div style="background: white; padding: 1rem; border-radius: 8px; margin: 0.5rem 0; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <strong style="color: #1E3A8A;">{activity['action']}</strong><br>
                    <span style="color: #64748B; font-size: 0.875rem;">{activity['details']}</span>
                </div>
                <div style="text-align: right;">
                    <span style="color: {status_color}; font-weight: 600;">{activity['status']}</span><br>
                    <span style="color: #64748B; font-size: 0.75rem;">{activity['time']}</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

def render_footer():
    """渲染页脚"""
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        ### 📞 技术支持
        **邮箱:** support@smartai.edu<br>
        **电话:** 400-123-4567
        """)
    
    with col2:
        st.markdown("""
        ### 📚 使用帮助
        - [用户手册](https://docs.smartai.edu)
        - [常见问题](https://faq.smartai.edu)
        - [更新日志](https://changelog.smartai.edu)
        """)
    
    with col3:
        st.markdown("""
        ### ℹ️ 系统信息
        **版本:** v1.0.0<br>
        **最后更新:** 2024-09-13
        """)

def render_dashboard():
    """渲染主界面内容（登录后显示）"""
    # 加载CSS和初始化
    load_custom_css()
    init_session_state()
    
    # Inject pollers for active jobs
    inject_pollers_for_active_jobs()
    
    # 渲染页面各个部分
    render_hero_section()
    render_user_welcome()
    
    st.markdown("---")
    render_statistics_overview()
    
    st.markdown("---")
    render_feature_cards()
    
    st.markdown("---")
    render_upload_section()
    
    st.markdown("---")
    render_quick_preview()
    
    st.markdown("---")
    render_quick_actions()
    
    st.markdown("---")
    render_recent_activities()
    
    render_footer()

def main():
    """主函数 - 应用入口点"""
    # 检查登录状态
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    
    # 如果未登录，重定向到登录页面
    if not st.session_state.logged_in:
        st.switch_page("pages/login.py")
    else:
        # 如果已登录，显示主界面内容
        render_dashboard()

if __name__ == "__main__":
    main()