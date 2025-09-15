"""
可视化分析界面 (pages/visualization.py)

功能包括：
1. 成绩统计概览
2. 题目分析
3. 学生表现
4. 交互功能
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import altair as alt

# 导入自定义模块
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.data_loader import StudentScore, QuestionAnalysis, AssignmentStats, load_sample_data
from utils.chart_components import (
    create_score_distribution_chart, create_grade_pie_chart, 
    create_question_accuracy_chart, create_knowledge_heatmap_chart,
    create_error_analysis_chart, create_trend_chart, create_difficulty_scatter_chart
)

# 页面配置
st.set_page_config(
    page_title="SmarTAI - 可视化分析",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
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
            padding: 1rem;
        }
        .stat-card {
            background: white;
            padding: 1.5rem;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            text-align: center;
            border-top: 4px solid #1E3A8A;
            transition: all 0.3s ease;
        }
        .stat-card:hover {
            transform: translateY(-4px);
            box-shadow: 0 8px 15px rgba(0, 0, 0, 0.15);
        }
        .stat-value {
            font-size: 2.5rem;
            font-weight: 700;
            color: #1E3A8A;
            margin-bottom: 0.25rem;
        }
        .stat-label {
            font-size: 0.875rem;
            color: #64748B;
            text-transform: uppercase;
            font-weight: 600;
            letter-spacing: 0.05em;
        }
        .chart-container {
            background: white;
            padding: 1.5rem;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            margin: 1rem 0;
        }
        .filter-container {
            background: white;
            padding: 1rem;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            margin-bottom: 1rem;
        }
        .breadcrumb {
            background: white;
            padding: 1rem;
            border-radius: 8px;
            margin-bottom: 1.5rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        </style>
        """, unsafe_allow_html=True)

def init_session_state():
    """初始化会话状态"""
    if 'sample_data' not in st.session_state:
        with st.spinner("加载数据中..."):
            st.session_state.sample_data = load_sample_data()
    
    if 'selected_class' not in st.session_state:
        st.session_state.selected_class = "全部班级"
    
    if 'selected_time_range' not in st.session_state:
        st.session_state.selected_time_range = "全部时间"
    
    if 'selected_question_type' not in st.session_state:
        st.session_state.selected_question_type = "全部题型"

def render_breadcrumb():
    """渲染面包屑导航"""
    st.markdown("""
    <div class="breadcrumb">
        <a href="/" style="text-decoration: none; color: #666;">🏠 首页</a>
        <span style="margin: 0 0.5rem; color: #666;">></span>
        <span style="color: #1E3A8A; font-weight: 600;">📈 可视化分析</span>
    </div>
    """, unsafe_allow_html=True)

def render_header():
    """渲染页面头部"""
    col1, col2, col3 = st.columns([2, 3, 2])
    
    with col1:
        if st.button("🏠 返回首页", type="secondary"):
            st.switch_page("main.py")
    
    with col2:
        st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>📈 可视化分析</h1>", 
                   unsafe_allow_html=True)
    
    with col3:
        if st.button("📊 评分报告", type="primary"):
            st.switch_page("pages/score_report.py")

def render_sidebar_filters():
    """渲染侧边栏筛选器"""
    st.sidebar.header("🔧 筛选器")
    
    # 显示当前筛选状态
    active_filters = []
    if st.session_state.selected_class != "全部班级":
        active_filters.append(f"📚 {st.session_state.selected_class}")
    if st.session_state.selected_time_range != "全部时间":
        active_filters.append(f"📅 {st.session_state.selected_time_range}")
    if st.session_state.selected_question_type != "全部题型":
        active_filters.append(f"📝 {st.session_state.selected_question_type}")
    
    if active_filters:
        st.sidebar.success(f"✅ 已应用 {len(active_filters)} 个筛选条件")
        with st.sidebar.expander("🔍 查看当前筛选"):
            for filter_desc in active_filters:
                st.write(f"- {filter_desc}")
    else:
        st.sidebar.info("🔄 显示全部数据")
    
    # 班级筛选
    classes = ["全部班级", "计算机科学1班", "计算机科学2班", "软件工程1班", "数据科学班"]
    selected_class = st.sidebar.selectbox(
        "📚 选择班级",
        classes,
        index=classes.index(st.session_state.selected_class),
        key="class_filter"
    )
    # 检测是否有变化
    if selected_class != st.session_state.selected_class:
        st.session_state.selected_class = selected_class
        st.rerun()  # 立即更新界面
    
    # 时间范围筛选
    time_ranges = ["全部时间", "最近一周", "最近一月", "最近三月", "本学期"]
    selected_time_range = st.sidebar.selectbox(
        "📅 时间范围",
        time_ranges,
        index=time_ranges.index(st.session_state.selected_time_range),
        key="time_filter"
    )
    # 检测是否有变化
    if selected_time_range != st.session_state.selected_time_range:
        st.session_state.selected_time_range = selected_time_range
        st.rerun()  # 立即更新界面
    
    # 题型筛选
    question_types = ["全部题型", "concept", "calculation", "proof", "programming"]
    selected_question_type = st.sidebar.selectbox(
        "📝 题目类型",
        question_types,
        index=question_types.index(st.session_state.selected_question_type),
        key="question_type_filter"
    )
    # 检测是否有变化
    if selected_question_type != st.session_state.selected_question_type:
        st.session_state.selected_question_type = selected_question_type
        st.rerun()  # 立即更新界面
    
    # 重置筛选器按钮
    if st.sidebar.button("🔄 重置所有筛选", width='stretch'):
        st.session_state.selected_class = "全部班级"
        st.session_state.selected_time_range = "全部时间"
        st.session_state.selected_question_type = "全部题型"
        st.rerun()
    
    # 分析选项
    st.sidebar.header("📊 分析选项")
    
    show_outliers = st.sidebar.checkbox("显示异常值", value=True)
    show_trend = st.sidebar.checkbox("显示趋势线", value=True)
    show_confidence = st.sidebar.checkbox("显示置信区间", value=False)
    
    # 导出选项
    st.sidebar.header("📤 导出选项")
    
    if st.sidebar.button("📄 生成分析报告", width='stretch'):
        generate_analysis_report()
    
    if st.sidebar.button("📊 导出飞书表格", width='stretch'):
        export_to_feishu()
    
    if st.sidebar.button("📈 下载图表", width='stretch'):
        download_charts()
    
    return {
        'class': selected_class,
        'time_range': selected_time_range,
        'question_type': selected_question_type,
        'show_outliers': show_outliers,
        'show_trend': show_trend,
        'show_confidence': show_confidence
    }

def filter_data_by_selections(data: Dict[str, Any], filters: Dict[str, Any]) -> Dict[str, Any]:
    """根据筛选条件过滤数据"""
    from utils.data_loader import StudentScore
    
    students = data['student_scores']
    question_analysis = data['question_analysis'] 
    assignment_stats = data['assignment_stats']
    
    # 按题型筛选学生数据和题目分析
    if filters['question_type'] != '全部题型':
        # 筛选学生数据中的相关题目
        filtered_students = []
        for student in students:
            filtered_questions = [
                q for q in student.questions 
                if q['question_type'] == filters['question_type']
            ]
            if filtered_questions:
                # 创建新的学生对象，只包含筛选后的题目
                filtered_student = StudentScore(
                    student_id=student.student_id,
                    student_name=student.student_name,
                    total_score=sum(q['score'] for q in filtered_questions),
                    max_score=sum(q['max_score'] for q in filtered_questions),
                    submit_time=student.submit_time,
                    questions=filtered_questions,
                    need_review=student.need_review,
                    confidence_score=student.confidence_score
                )
                filtered_students.append(filtered_student)
        
        students = filtered_students
        
        # 筛选题目分析数据
        question_analysis = [
            qa for qa in question_analysis 
            if qa.question_type == filters['question_type']
        ]
    
    # 按班级筛选（模拟实现，实际应用中需要实际的班级数据）
    if filters['class'] != '全部班级':
        # 根据班级名称筛选学生（这里使用模拟逻辑）
        class_mapping = {
            '计算机科学1班': lambda s: s.student_id.endswith(('01', '11', '21', '31', '41')),
            '计算机科学2班': lambda s: s.student_id.endswith(('02', '12', '22', '32', '42')),
            '软件工程1班': lambda s: s.student_id.endswith(('03', '13', '23', '33', '43')),
            '数据科学班': lambda s: s.student_id.endswith(('04', '14', '24', '34', '44'))
        }
        
        if filters['class'] in class_mapping:
            students = [s for s in students if class_mapping[filters['class']](s)]
    
    # 按时间范围筛选（模拟实现）
    if filters['time_range'] != '全部时间':
        from datetime import datetime, timedelta
        now = datetime.now()
        
        time_filters = {
            '最近一周': now - timedelta(weeks=1),
            '最近一月': now - timedelta(days=30),
            '最近三月': now - timedelta(days=90),
            '本学期': now - timedelta(days=120)
        }
        
        if filters['time_range'] in time_filters:
            cutoff_date = time_filters[filters['time_range']]
            students = [s for s in students if s.submit_time >= cutoff_date]
    
    return {
        'student_scores': students,
        'question_analysis': question_analysis,
        'assignment_stats': assignment_stats
    }

def render_statistics_overview(students: List[StudentScore], assignment_stats: AssignmentStats, filters: Dict[str, Any]):
    """渲染统计概览"""
    st.markdown("## 📊 成绩统计概览")
    
    # 显示筛选状态和数量信息
    filter_active = (filters['class'] != '全部班级' or 
                    filters['time_range'] != '全部时间' or 
                    filters['question_type'] != '全部题型')
    
    if filter_active:
        filter_info = []
        if filters['class'] != '全部班级':
            filter_info.append(f"📚 {filters['class']}")
        if filters['time_range'] != '全部时间':
            filter_info.append(f"📅 {filters['time_range']}")
        if filters['question_type'] != '全部题型':
            filter_info.append(f"📝 {filters['question_type']}")
        
        st.info(f"🔍 **筛选后显示**: {' | '.join(filter_info)} | 共 {len(students)} 名学生")
    else:
        st.success(f"🔄 **显示全部数据**: 共 {len(students)} 名学生")
    
    # 计算统计数据
    if not students:  # 处理空数据情况
        st.warning("⚠️ 没有符合筛选条件的数据")
        return
    
    scores = [s.percentage for s in students]
    avg_score = np.mean(scores)
    max_score = np.max(scores)
    min_score = np.min(scores)
    std_score = np.std(scores)
    pass_rate = len([s for s in scores if s >= 60]) / len(scores) * 100
    excellence_rate = len([s for s in scores if s >= 85]) / len(scores) * 100
    
    # 显示统计卡片
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    with col1:
        st.markdown("""
        <div class="stat-card">
            <div class="stat-value">{}</div>
            <div class="stat-label">提交人数</div>
        </div>
        """.format(len(students)), unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="stat-card">
            <div class="stat-value">{:.1f}%</div>
            <div class="stat-label">平均分</div>
        </div>
        """.format(avg_score), unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="stat-card">
            <div class="stat-value">{:.1f}%</div>
            <div class="stat-label">最高分</div>
        </div>
        """.format(max_score), unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div class="stat-card">
            <div class="stat-value">{:.1f}%</div>
            <div class="stat-label">最低分</div>
        </div>
        """.format(min_score), unsafe_allow_html=True)
    
    with col5:
        st.markdown("""
        <div class="stat-card">
            <div class="stat-value">{:.1f}%</div>
            <div class="stat-label">及格率</div>
        </div>
        """.format(pass_rate), unsafe_allow_html=True)
    
    with col6:
        st.markdown("""
        <div class="stat-card">
            <div class="stat-value">{:.1f}%</div>
            <div class="stat-label">优秀率</div>
        </div>
        """.format(excellence_rate), unsafe_allow_html=True)

def render_score_distribution_analysis(students: List[StudentScore]):
    """渲染成绩分布分析"""
    st.markdown("## 📈 成绩分布分析")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 成绩分布直方图")
        try:
            fig = create_score_distribution_chart(students)
            st.plotly_chart(fig, width='stretch')
        except Exception as e:
            st.error(f"生成分布图时出错: {str(e)}")
    
    with col2:
        st.markdown("### 成绩等级分布")
        try:
            fig = create_grade_pie_chart(students)
            st.plotly_chart(fig, width='stretch')
        except Exception as e:
            st.error(f"生成饼图时出错: {str(e)}")

def render_question_analysis(question_analysis: List[QuestionAnalysis]):
    """渲染题目分析"""
    st.markdown("## 🎯 题目分析")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 各题正确率")
        try:
            fig = create_question_accuracy_chart(question_analysis)
            st.plotly_chart(fig, width='stretch')
        except Exception as e:
            st.error(f"生成正确率图时出错: {str(e)}")
    
    with col2:
        st.markdown("### 知识点掌握度热力图")
        try:
            fig = create_knowledge_heatmap_chart(question_analysis)
            st.plotly_chart(fig, width='stretch')
        except Exception as e:
            st.error(f"生成热力图时出错: {str(e)}")
    
    # 题目难度vs正确率分析
    st.markdown("### 题目难度 vs 正确率分析")
    try:
        fig = create_difficulty_scatter_chart(question_analysis)
        st.plotly_chart(fig, width='stretch')
    except Exception as e:
        st.error(f"生成散点图时出错: {str(e)}")
    
    # 易错题排行榜
    render_error_analysis_section(question_analysis)

def render_error_analysis_section(question_analysis: List[QuestionAnalysis]):
    """渲染错误分析部分"""
    st.markdown("### 📋 易错题排行榜")
    
    # 错误分析图表 - 全宽显示
    try:
        fig = create_error_analysis_chart(question_analysis)
        st.plotly_chart(fig, width='stretch')
    except Exception as e:
        st.error(f"生成错误分析图时出错: {str(e)}")
    
    st.markdown("---")
    
    # 难度最高的题目 - 使用原生Streamlit组件
    st.markdown("#### 🎯 难度最高的题目 (Top 10)")
    
    # 按难度排序
    sorted_questions = sorted(question_analysis, key=lambda x: x.difficulty, reverse=True)[:10]
    
    if not sorted_questions:
        st.info("暂无题目数据")
        return
    
    # 每行显示2个题目卡片
    for i in range(0, len(sorted_questions), 2):
        cols = st.columns(2)
        
        for j, col in enumerate(cols):
            if i + j < len(sorted_questions):
                qa = sorted_questions[i + j]
                render_question_difficulty_card(qa, i + j + 1, col)

def render_question_difficulty_card(qa, rank: int, container):
    """渲染单个题目难度卡片 - 使用原生Streamlit组件"""
    difficulty_level = qa.difficulty_level
    
    with container:
        # 使用Streamlit原生组件替代复杂HTML
        with st.container():
            # 题目标题区域
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"**#{rank} {qa.question_id}**")
            with col2:
                # 根据难度设置颜色
                if difficulty_level == "困难":
                    st.error(difficulty_level)
                elif difficulty_level == "中等":
                    st.warning(difficulty_level)
                else:
                    st.success(difficulty_level)
            
            # 题目信息
            st.markdown(f"**题目主题:** {qa.topic}")
            
            # 指标展示
            metric_col1, metric_col2, metric_col3 = st.columns(3)
            with metric_col1:
                st.metric("难度系数", f"{qa.difficulty:.2f}")
            with metric_col2:
                st.metric("正确率", f"{qa.correct_rate:.1%}")
            with metric_col3:
                st.metric("平均分", f"{qa.avg_score:.1f}/{qa.max_score}")
            
            # 常见错误
            if qa.common_errors:
                st.markdown("**常见错误:**")
                # 使用列表展示错误
                for error in qa.common_errors[:3]:
                    st.markdown(f"- {error}")
            
            st.markdown("---")  # 分隔线

def render_student_performance_analysis(students: List[StudentScore]):
    """渲染学生表现分析"""
    st.markdown("## 👥 学生表现分析")
    
    # 成绩排名表 - 全宽显示
    st.markdown("### 📊 成绩排名表")
    
    # 创建排名数据
    ranking_data = []
    for i, student in enumerate(sorted(students, key=lambda x: x.total_score, reverse=True), 1):
        ranking_data.append({
            "排名": i,
            "学号": student.student_id,
            "姓名": student.student_name,
            "总分": f"{student.total_score:.1f}",
            "百分比": f"{student.percentage:.1f}%",
            "等级": student.grade_level,
            "置信度": f"{student.confidence_score:.1%}",
            "需复核": "是" if student.need_review else "否"
        })
    
    # 创建DataFrame并显示
    df = pd.DataFrame(ranking_data)
    
    # 使用st.dataframe显示可排序的表格
    st.dataframe(
        df,
        width='stretch',
        height=400,
        column_config={
            "排名": st.column_config.NumberColumn("排名", format="%d"),
            "总分": st.column_config.NumberColumn("总分", format="%.1f"),
            "百分比": st.column_config.ProgressColumn("百分比", format="%.1f%%", min_value=0, max_value=100),
            "置信度": st.column_config.ProgressColumn("置信度", format="%.1%%", min_value=0, max_value=1),
        }
    )
    
    # 需要关注的学生 - 横向卡片式展示
    st.markdown("---")
    st.markdown("### ⚠️ 需要关注的学生")
    
    # 筛选需要关注的学生（低分或低置信度）
    attention_students = [
        s for s in students 
        if s.percentage < 60 or s.confidence_score < 0.75 or s.need_review
    ]
    
    if not attention_students:
        st.success("🎉 所有学生表现良好，无需特别关注！")
        return
    
    # 显示总体统计
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("需关注学生", len(attention_students), f"{len(attention_students)/len(students)*100:.1f}%")
    with col2:
        failing_count = len([s for s in attention_students if s.percentage < 60])
        st.metric("不及格人数", failing_count)
    with col3:
        low_confidence_count = len([s for s in attention_students if s.confidence_score < 0.75])
        st.metric("低置信度人数", low_confidence_count)
    
    st.markdown("")
    
    # 按问题严重程度分层展示
    # 第一层：不及格学生
    failing_students = [s for s in attention_students if s.percentage < 60]
    if failing_students:
        st.markdown("#### 🚨 不及格学生 (需重点关注)")
        render_student_cards_horizontal(failing_students, "danger")
        st.markdown("")
    
    # 第二层：低置信度但及格的学生
    low_confidence_students = [
        s for s in attention_students 
        if s.percentage >= 60 and s.confidence_score < 0.75
    ]
    if low_confidence_students:
        st.markdown("#### 🟡 评分置信度较低学生 (建议复核)")
        render_student_cards_horizontal(low_confidence_students, "warning")
        st.markdown("")
    
    # 第三层：需要复核的学生
    review_students = [
        s for s in attention_students 
        if s.need_review and s.percentage >= 60 and s.confidence_score >= 0.75
    ]
    if review_students:
        st.markdown("#### 📋 其他需复核学生")
        render_student_cards_horizontal(review_students, "info")

def render_student_cards_horizontal(students: List[StudentScore], alert_type: str = "info"):
    """横向展示学生卡片 - 使用原生Streamlit组件"""
    # 每行显示3个学生卡片
    for i in range(0, len(students), 3):
        cols = st.columns(3)
        
        for j, col in enumerate(cols):
            if i + j < len(students):
                student = students[i + j]
                
                # 确定关注原因
                reasons = []
                if student.percentage < 60:
                    reasons.append("不及格")
                if student.confidence_score < 0.75:
                    reasons.append("低置信度")
                if student.need_review:
                    reasons.append("需复核")
                
                reason_text = ", ".join(reasons)
                
                with col:
                    # 使用原生Streamlit组件
                    with st.container():
                        # 根据alert_type设置显示样式
                        if alert_type == "danger":
                            st.error(f"🚨 {student.student_name}")
                        elif alert_type == "warning":
                            st.warning(f"🟡 {student.student_name}")
                        else:
                            st.info(f"📋 {student.student_name}")
                        
                        # 学生信息
                        st.markdown(f"**学号:** {student.student_id}")
                        
                        # 成绩信息
                        col_score, col_grade = st.columns(2)
                        with col_score:
                            st.metric("成绩", f"{student.percentage:.1f}%")
                        with col_grade:
                            st.metric("等级", student.grade_level)
                        
                        # 置信度
                        st.metric("置信度", f"{student.confidence_score:.1%}")
                        
                        # 关注原因
                        st.markdown(f"**关注原因:** {reason_text}")
                        
                        st.markdown("")  # 添加间距

def render_trend_analysis(students: List[StudentScore]):
    """渲染趋势分析"""
    st.markdown("## 📈 成绩趋势分析")
    
    try:
        fig = create_trend_chart(students)
        st.plotly_chart(fig, width='stretch')
    except Exception as e:
        st.error(f"生成趋势图时出错: {str(e)}")
    
    # 进步和退步学生分析
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📈 进步较大的学生")
        # 模拟进步数据（实际应用中需要历史数据对比）
        progress_students = [
            {"姓名": "张同学", "当前成绩": 85.5, "进步幅度": "+15.2%"},
            {"姓名": "李同学", "当前成绩": 78.3, "进步幅度": "+12.8%"},
            {"姓名": "王同学", "当前成绩": 91.2, "进步幅度": "+10.5%"},
            {"姓名": "刘同学", "当前成绩": 73.7, "进步幅度": "+9.3%"},
            {"姓名": "陈同学", "当前成绩": 87.1, "进步幅度": "+8.7%"}
        ]
        
        for student in progress_students:
            st.markdown(f"""
            **{student['姓名']}**
            - 当前成绩: {student['当前成绩']}%
            - <span style="color: #10B981;">进步: {student['进步幅度']}</span>
            """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("### 📉 需要关注的学生")
        # 模拟退步数据
        decline_students = [
            {"姓名": "赵同学", "当前成绩": 65.2, "变化": "-8.5%"},
            {"姓名": "孙同学", "当前成绩": 58.9, "变化": "-12.3%"},
            {"姓名": "周同学", "当前成绩": 72.1, "变化": "-6.7%"},
            {"姓名": "吴同学", "当前成绩": 61.4, "变化": "-9.1%"},
            {"姓名": "郑同学", "当前成绩": 69.8, "变化": "-5.2%"}
        ]
        
        for student in decline_students:
            st.markdown(f"""
            **{student['姓名']}**
            - 当前成绩: {student['当前成绩']}%
            - <span style="color: #EF4444;">变化: {student['变化']}</span>
            """, unsafe_allow_html=True)

def render_interactive_analysis():
    """渲染交互式分析"""
    st.markdown("## 🔄 交互式分析")
    
    # 添加交互式筛选器
    col1, col2, col3 = st.columns(3)
    
    with col1:
        score_range = st.slider(
            "成绩范围",
            min_value=0,
            max_value=100,
            value=(60, 100),
            step=5
        )
    
    with col2:
        confidence_threshold = st.slider(
            "置信度阈值",
            min_value=0.0,
            max_value=1.0,
            value=0.75,
            step=0.05,
            format="%.2f"
        )
    
    with col3:
        chart_type = st.selectbox(
            "图表类型",
            ["散点图", "箱线图", "小提琴图", "热力图"]
        )
    
    # 根据选择生成对应图表
    students = st.session_state.sample_data['student_scores']
    
    # 根据筛选条件过滤数据
    filtered_students = [
        s for s in students 
        if score_range[0] <= s.percentage <= score_range[1] 
        and s.confidence_score >= confidence_threshold
    ]
    
    if filtered_students:
        if chart_type == "散点图":
            render_interactive_scatter(filtered_students)
        elif chart_type == "箱线图":
            render_interactive_boxplot(filtered_students)
        elif chart_type == "小提琴图":
            render_interactive_violin(filtered_students)
        elif chart_type == "热力图":
            render_interactive_heatmap(filtered_students)
    else:
        st.warning("⚠️ 没有符合筛选条件的数据")

def render_interactive_scatter(students: List[StudentScore]):
    """渲染交互式散点图"""
    # 准备数据
    data = []
    for student in students:
        for q in student.questions:
            data.append({
                'student_name': student.student_name,
                'question_id': q['question_id'],
                'score_rate': q['score'] / q['max_score'],
                'confidence': q['confidence'],
                'question_type': q['question_type']
            })
    
    df = pd.DataFrame(data)
    
    # 创建散点图
    fig = px.scatter(
        df,
        x='confidence',
        y='score_rate',
        color='question_type',
        size='score_rate',
        hover_data=['student_name', 'question_id'],
        title="学生答题置信度 vs 得分率",
        labels={
            'confidence': '置信度',
            'score_rate': '得分率',
            'question_type': '题目类型'
        }
    )
    
    fig.update_layout(
        font=dict(family="Noto Sans SC", size=12),
        plot_bgcolor='white',
        paper_bgcolor='white'
    )
    
    st.plotly_chart(fig, width='stretch')

def render_interactive_boxplot(students: List[StudentScore]):
    """渲染交互式箱线图"""
    # 按题目类型分组数据
    type_scores = {}
    for student in students:
        for q in student.questions:
            qtype = q['question_type']
            if qtype not in type_scores:
                type_scores[qtype] = []
            type_scores[qtype].append(q['score'] / q['max_score'] * 100)
    
    # 创建箱线图
    fig = go.Figure()
    
    colors = ['#1E3A8A', '#10B981', '#F59E0B', '#EF4444']
    
    for i, (qtype, scores) in enumerate(type_scores.items()):
        fig.add_trace(go.Box(
            y=scores,
            name=qtype,
            marker_color=colors[i % len(colors)],
            boxpoints='outliers'
        ))
    
    fig.update_layout(
        title="各题型得分分布箱线图",
        yaxis_title="得分率 (%)",
        xaxis_title="题目类型",
        font=dict(family="Noto Sans SC", size=12),
        plot_bgcolor='white',
        paper_bgcolor='white'
    )
    
    st.plotly_chart(fig, width='stretch')

def render_interactive_violin(students: List[StudentScore]):
    """渲染交互式小提琴图"""
    # 准备数据
    data = []
    for student in students:
        data.append({
            'grade_level': student.grade_level,
            'percentage': student.percentage,
            'confidence': student.confidence_score
        })
    
    df = pd.DataFrame(data)
    
    # 创建小提琴图
    fig = px.violin(
        df,
        x='grade_level',
        y='percentage',
        title="各成绩等级分布小提琴图",
        labels={
            'grade_level': '成绩等级',
            'percentage': '成绩百分比'
        }
    )
    
    fig.update_layout(
        font=dict(family="Noto Sans SC", size=12),
        plot_bgcolor='white',
        paper_bgcolor='white'
    )
    
    st.plotly_chart(fig, use_container_width=True)

def render_interactive_heatmap(students: List[StudentScore]):
    """渲染交互式热力图"""
    # 创建学生-题目得分矩阵
    student_names = [s.student_name[:3] + "..." for s in students[:20]]  # 只显示前20名学生
    question_ids = list(set([q['question_id'] for s in students for q in s.questions]))
    question_ids.sort()
    
    # 构建矩阵
    matrix = []
    for student in students[:20]:
        row = []
        student_questions = {q['question_id']: q['score']/q['max_score'] for q in student.questions}
        for qid in question_ids:
            row.append(student_questions.get(qid, 0))
        matrix.append(row)
    
    # 创建热力图
    fig = go.Figure(data=go.Heatmap(
        z=matrix,
        x=question_ids,
        y=student_names,
        colorscale='RdYlGn',
        reversescale=False,
        showscale=True,
        colorbar=dict(title="得分率")
    ))
    
    fig.update_layout(
        title="学生-题目得分热力图",
        xaxis_title="题目编号",
        yaxis_title="学生姓名",
        font=dict(family="Noto Sans SC", size=12),
        plot_bgcolor='white',
        paper_bgcolor='white'
    )
    
    st.plotly_chart(fig, width='stretch')

def export_to_feishu():
    """导出到飞书多维表格"""
    with st.spinner("正在生成飞书多维表格数据..."):
        import time
        time.sleep(2)
        
        # 模拟生成飞书表格结构
        feishu_data = {
            "table_name": "SmarTAI_成绩分析报告",
            "sheets": [
                {
                    "sheet_name": "学生成绩汇总",
                    "columns": ["学号", "姓名", "总分", "百分比", "等级", "置信度", "复核状态"],
                    "records": 50
                },
                {
                    "sheet_name": "题目分析",
                    "columns": ["题目编号", "题目类型", "正确率", "难度系数", "平均分"],
                    "records": 12
                },
                {
                    "sheet_name": "知识点掌握度",
                    "columns": ["知识点", "掌握度", "题目数量", "平均得分率"],
                    "records": 10
                },
                {
                    "sheet_name": "易错题统计",
                    "columns": ["错误类型", "出现次数", "影响学生数", "建议改进措施"],
                    "records": 8
                }
            ],
            "dashboard_url": "https://feishu.example.com/dashboard/smartai_analysis_2024",
            "share_permissions": ["课程负责人", "任课教师", "教学管理者"]
        }
        
    st.success(f"✅ 数据已成功导出到飞书多维表格！")
    
    # 显示导出结果
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**已创建的表格:**")
        for sheet in feishu_data["sheets"]:
            st.markdown(f"- {sheet['sheet_name']}: {sheet['records']}条记录")
    
    with col2:
        st.markdown("**共享权限:**")
        for permission in feishu_data["share_permissions"]:
            st.markdown(f"- {permission}")
    
    # 仪表盘快照链接
    st.info(f"🔗 仪表盘快照链接: {feishu_data['dashboard_url']}")
    
    # 显示协同功能
    st.markdown("#### 🤝 协同功能")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📋 分配复核任务", use_container_width=True):
            st.success("已向3名教师分配复核任务")
    
    with col2:
        if st.button("📞 催办提醒", use_container_width=True):
            st.info("已发送催办提醒给相关人员")
    
    with col3:
        if st.button("📊 生成教学改进计划", use_container_width=True):
            st.success("基于易错题分析已生成改进建议")
    
    return feishu_data

def generate_analysis_report():
    """生成分析报告"""
    with st.spinner("生成分析报告中..."):
        import time
        time.sleep(2)  # 模拟处理时间
        
        # 生成报告结构
        report_sections = [
            "📊 班级整体表现概览",
            "📈 成绩分布分析",
            "🎯 各题目难度与正确率分析", 
            "🧠 知识点掌握情况",
            "⚠️ 易错题型与典型错误",
            "👥 需要关注的学生名单",
            "💡 教学改进建议",
            "📋 下一步行动计划"
        ]
        
    st.success("✅ 分析报告已生成！报告包含了完整的统计数据、图表和建议。")
    
    # 显示报告章节
    with st.expander("📋 查看报告目录"):
        for i, section in enumerate(report_sections, 1):
            st.markdown(f"{i}. {section}")
    
    # 生成补救计划
    st.markdown("#### 🎯 自动生成的补救计划")
    
    remedial_plans = [
        {
            "knowledge_point": "数据结构基础",
            "weakness_level": "高",
            "affected_students": 12,
            "recommended_actions": [
                "安排专项辅导课程",
                "提供额外练习材料", 
                "组织学习小组互助"
            ]
        },
        {
            "knowledge_point": "算法复杂度分析",
            "weakness_level": "中",
            "affected_students": 8,
            "recommended_actions": [
                "增加相关例题讲解",
                "提供可视化学习资源"
            ]
        }
    ]
    
    for plan in remedial_plans:
        with st.container():
            level_color = "#EF4444" if plan["weakness_level"] == "高" else "#F59E0B"
            st.markdown(f"""
            <div style="border-left: 4px solid {level_color}; padding: 1rem; background: #f8f9fa; margin: 0.5rem 0;">
                <h4 style="color: {level_color}; margin: 0;">{plan['knowledge_point']} - {plan['weakness_level']}薄弱</h4>
                <p style="margin: 0.5rem 0;"><strong>影响学生:</strong> {plan['affected_students']}人</p>
                <p style="margin: 0;"><strong>建议措施:</strong></p>
                <ul style="margin: 0.5rem 0;">
            """, unsafe_allow_html=True)
            
            for action in plan["recommended_actions"]:
                st.markdown(f"<li>{action}</li>", unsafe_allow_html=True)
            
            st.markdown("</ul></div>", unsafe_allow_html=True)

def download_charts():
    """下载图表"""
    with st.spinner("准备图表下载..."):
        import time
        time.sleep(1)
    st.success("📈 图表下载已开始！所有图表将以PNG格式保存。")

# Enhanced drill-down analysis functions
def render_knowledge_point_drilldown(students: List[StudentScore]):
    """知识点钻取分析"""
    # 统计各知识点的掌握情况
    knowledge_stats = {}
    
    for student in students:
        for question in student.questions:
            for kp in question['knowledge_points']:
                if kp not in knowledge_stats:
                    knowledge_stats[kp] = {'total_score': 0, 'total_possible': 0, 'student_count': 0}
                knowledge_stats[kp]['total_score'] += question['score']
                knowledge_stats[kp]['total_possible'] += question['max_score']
                knowledge_stats[kp]['student_count'] += 1
    
    # 计算掌握率
    knowledge_mastery = {}
    for kp, stats in knowledge_stats.items():
        mastery_rate = (stats['total_score'] / stats['total_possible']) * 100 if stats['total_possible'] > 0 else 0
        knowledge_mastery[kp] = {
            'mastery_rate': mastery_rate,
            'question_count': stats['student_count']
        }
    
    # 按掌握率排序显示
    sorted_knowledge = sorted(knowledge_mastery.items(), key=lambda x: x[1]['mastery_rate'])
    
    st.markdown("**知识点掌握情况** (按掌握率升序):")
    
    for kp, data in sorted_knowledge[:5]:  # 显示最需要关注的前5个
        mastery_rate = data['mastery_rate']
        color = "#EF4444" if mastery_rate < 60 else "#F59E0B" if mastery_rate < 75 else "#10B981"
        
        st.markdown(f"""
        <div style="margin: 0.25rem 0; padding: 0.5rem; border-radius: 4px; background: #f8f9fa;">
            <strong>{kp}</strong><br>
            <span style="color: {color}; font-weight: bold;">{mastery_rate:.1f}%</span> 
            <small>({data['question_count']}道题)</small>
        </div>
        """, unsafe_allow_html=True)

def render_question_type_drilldown(students: List[StudentScore]):
    """题目类型钻取分析"""
    type_stats = {}
    
    for student in students:
        for question in student.questions:
            qtype = question['question_type']
            if qtype not in type_stats:
                type_stats[qtype] = {'total_score': 0, 'total_possible': 0, 'count': 0}
            type_stats[qtype]['total_score'] += question['score']
            type_stats[qtype]['total_possible'] += question['max_score']
            type_stats[qtype]['count'] += 1
    
    type_names = {
        'concept': '概念理解',
        'calculation': '计算能力',
        'proof': '证明推理',
        'programming': '编程实现'
    }
    
    st.markdown("**各类题型表现:**")
    
    for qtype, stats in type_stats.items():
        avg_rate = (stats['total_score'] / stats['total_possible']) * 100 if stats['total_possible'] > 0 else 0
        color = "#EF4444" if avg_rate < 60 else "#F59E0B" if avg_rate < 75 else "#10B981"
        
        st.markdown(f"""
        <div style="margin: 0.25rem 0; padding: 0.5rem; border-radius: 4px; background: #f8f9fa;">
            <strong>{type_names.get(qtype, qtype)}</strong><br>
            <span style="color: {color}; font-weight: bold;">{avg_rate:.1f}%</span>
            <small>({stats['count']}道题)</small>
        </div>
        """, unsafe_allow_html=True)

def render_error_type_drilldown(students: List[StudentScore]):
    """错误类型钻取分析"""
    error_stats = {}
    
    for student in students:
        for question in student.questions:
            for error in question.get('errors', []):
                if error not in error_stats:
                    error_stats[error] = {'count': 0, 'students': set()}
                error_stats[error]['count'] += 1
                error_stats[error]['students'].add(student.student_id)
    
    # 按出现次数排序
    sorted_errors = sorted(error_stats.items(), key=lambda x: x[1]['count'], reverse=True)
    
    st.markdown("**常见错误类型排行:**")
    
    for error, data in sorted_errors[:5]:  # 显示前5个最常见错误
        affected_students = len(data['students'])
        priority_color = "#EF4444" if data['count'] > 10 else "#F59E0B" if data['count'] > 5 else "#10B981"
        
        st.markdown(f"""
        <div style="margin: 0.25rem 0; padding: 0.5rem; border-radius: 4px; background: #f8f9fa; border-left: 3px solid {priority_color};">
            <strong>{error}</strong><br>
            <span style="color: {priority_color}; font-weight: bold;">{data['count']}次</span>
            <small>(影响{affected_students}名学生)</small>
        </div>
        """, unsafe_allow_html=True)

def render_enhanced_error_analysis_section(question_analysis: List[QuestionAnalysis]):
    """渲染增强的错误分析部分，支持按错误率排序和典型错误样例"""
    st.markdown("### 📋 易错题排行榜 - 智能识别教学薄弱环节")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        try:
            fig = create_error_analysis_chart(question_analysis)
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"生成错误分析图时出错: {str(e)}")
    
    with col2:
        # 按错误率排序显示易错题
        st.markdown("#### 🎯 按错误率排序的易错题")
        
        # 计算每道题的错误率
        error_rate_questions = []
        for qa in question_analysis:
            error_rate = 1 - qa.correct_rate
            error_rate_questions.append({
                'question_id': qa.question_id,
                'topic': qa.topic,
                'error_rate': error_rate,
                'correct_rate': qa.correct_rate,
                'difficulty': qa.difficulty,
                'common_errors': qa.common_errors
            })
        
        # 按错误率降序排序
        sorted_questions = sorted(error_rate_questions, key=lambda x: x['error_rate'], reverse=True)
        
        for i, q in enumerate(sorted_questions[:5], 1):
            error_rate_pct = q['error_rate'] * 100
            priority_color = "#EF4444" if error_rate_pct > 50 else "#F59E0B" if error_rate_pct > 30 else "#10B981"
            
            st.markdown(f"""
            <div style="border-left: 4px solid {priority_color}; padding: 0.75rem; margin: 0.5rem 0; background: #f8f9fa;">
                <strong>{i}. {q['question_id']} - {q['topic']}</strong><br>
                <span style="color: {priority_color}; font-weight: bold;">错误率: {error_rate_pct:.1f}%</span> 
                <small>(正确率: {q['correct_rate']:.1%})</small><br>
                <small><strong>典型错误:</strong> {', '.join(q['common_errors'][:2])}</small>
            </div>
            """, unsafe_allow_html=True)
    
    # 生成补救计划的建议
    render_remedial_plan_suggestions(sorted_questions[:3])

def render_remedial_plan_suggestions(difficult_questions):
    """生成针对易错题的补救计划建议"""
    st.markdown("#### 💡 自动生成的补救计划")
    
    # 基于易错题生成针对性建议
    remedial_suggestions = {
        "概念理解": {
            "icon": "🧠",
            "actions": ["加强基础概念讲解", "提供概念图和思维导图", "组织概念辨析练习"],
            "priority": "高"
        },
        "计算能力": {
            "icon": "🔢", 
            "actions": ["增加计算练习题", "讲解计算技巧和方法", "提供计算工具使用指导"],
            "priority": "中"
        },
        "算法设计": {
            "icon": "⚙️",
            "actions": ["提供算法可视化演示", "增加算法设计模式讲解", "安排算法实现练习"],
            "priority": "高"
        }
    }
    
    for topic, suggestion in remedial_suggestions.items():
        priority_color = "#EF4444" if suggestion["priority"] == "高" else "#F59E0B"
        
        with st.expander(f"{suggestion['icon']} {topic} - {suggestion['priority']}优先级补救计划"):
            st.markdown("**建议措施:**")
            for action in suggestion["actions"]:
                st.markdown(f"- {action}")
            
            # 显示相关的易错题
            related_questions = [q for q in difficult_questions if topic.lower() in q['topic'].lower()]
            if related_questions:
                st.markdown("**相关易错题:**")
                for q in related_questions[:2]:
                    st.markdown(f"- {q['question_id']}: 错误率 {(q['error_rate']*100):.1f}%")

def main():
    """主函数"""
    # 加载CSS和初始化
    load_css()
    init_session_state()
    
    # 渲染页面
    render_breadcrumb()
    render_header()
    
    # 侧边栏筛选器
    filters = render_sidebar_filters()
    
    # 获取数据
    data = st.session_state.sample_data
    filtered_data = filter_data_by_selections(data, filters)
    
    students = filtered_data['student_scores']
    question_analysis = filtered_data['question_analysis']
    assignment_stats = filtered_data['assignment_stats']
    
    # 渲染各个分析模块
    render_statistics_overview(students, assignment_stats, filters)
    
    # 只在有数据时显示其他分析
    if students:
        st.markdown("---")
        render_score_distribution_analysis(students)
        
        st.markdown("---")
        render_question_analysis(question_analysis)
        
        st.markdown("---")
        render_student_performance_analysis(students)
        
        st.markdown("---")
        render_trend_analysis(students)
        
        st.markdown("---")
        render_interactive_analysis()
    else:
        st.warning("⚠️ 没有符合筛选条件的数据，请调整筛选条件。")

if __name__ == "__main__":
    main()