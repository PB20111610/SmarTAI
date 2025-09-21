"""
历史批改记录增强版 (pages/history_enhanced.py)

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
    if 'draft_records' not in st.session_state:
        st.session_state.draft_records = {}  # 暂存记录
    
    if 'completed_records' not in st.session_state:
        st.session_state.completed_records = {}  # 完成记录
    
    # 从文件系统加载暂存记录（如果存在）
    load_draft_records_from_file()

def load_draft_records_from_file():
    """从文件系统加载暂存记录"""
    draft_file = "draft_records.json"
    if os.path.exists(draft_file):
        try:
            with open(draft_file, 'r', encoding='utf-8') as f:
                st.session_state.draft_records = json.load(f)
        except Exception as e:
            st.error(f"加载暂存记录失败: {e}")

def save_draft_records_to_file():
    """保存暂存记录到文件系统"""
    draft_file = "draft_records.json"
    try:
        with open(draft_file, 'w', encoding='utf-8') as f:
            json.dump(st.session_state.draft_records, f, ensure_ascii=False, indent=2, default=str)
    except Exception as e:
        st.error(f"保存暂存记录失败: {e}")

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
            load_draft_records_from_file()
            sync_completed_records()
            st.success("记录已刷新！")
            st.rerun()

def sync_completed_records():
    """同步已完成的批改记录"""
    if "jobs" in st.session_state and st.session_state.jobs:
        for job_id, task_info in st.session_state.jobs.items():
            try:
                result = requests.get(f"{st.session_state.backend}/ai_grading/grade_result/{job_id}", timeout=10)
                result.raise_for_status()
                status = result.json().get("status", "未知")
                
                if status == "completed":
                    st.session_state.completed_records[job_id] = {
                        "task_name": task_info.get("name", "未知任务"),
                        "submitted_at": task_info.get("submitted_at", "未知时间"),
                        "completed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "status": status
                    }
            except Exception as e:
                continue

def create_draft_record(record_id: str, record_data: Dict[str, Any]):
    """创建暂存记录"""
    st.session_state.draft_records[record_id] = {
        "id": record_id,
        "name": record_data.get("name", "未命名记录"),
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "problem_data": record_data.get("problem_data", {}),
        "student_data": record_data.get("student_data", []),
        "preview_data": record_data.get("preview_data", {}),
        "manual_adjustments": record_data.get("manual_adjustments", {}),
        "status": "draft"
    }
    save_draft_records_to_file()

def render_tabs():
    """渲染主要标签页"""
    tab1, tab2, tab3 = st.tabs(["📝 暂存记录", "✅ 已完成批改", "📊 统计概览"])
    
    with tab1:
        render_draft_records()
    
    with tab2:
        render_completed_records()
    
    with tab3:
        render_statistics_overview()

def render_draft_records():
    """渲染暂存记录"""
    st.markdown("## 📝 暂存记录")
    st.markdown("这里显示已上传但尚未批改的作业记录，您可以预览、编辑或继续批改。")
    
    if not st.session_state.draft_records:
        st.info("暂无暂存记录。上传作业后会自动保存为暂存记录。")
        
        # 提供创建测试暂存记录的按钮
        if st.button("📁 创建测试暂存记录", type="primary"):
            test_record_id = f"draft_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            create_draft_record(test_record_id, {
                "name": "测试作业批改",
                "problem_data": {"题目数": 3, "总分": 100},
                "student_data": [{"学号": "S001", "姓名": "张三"}],
                "preview_data": {"识别率": "95%", "需要调整": 2}
            })
            st.success("测试暂存记录已创建！")
            st.rerun()
        return
    
    # 显示暂存记录列表
    for record_id, record in st.session_state.draft_records.items():
        with st.container():
            st.markdown(f"""
            <div style="background: white; padding: 1.5rem; border-radius: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); margin: 1rem 0; border-left: 4px solid #F59E0B;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <h3 style="color: #1E3A8A; margin: 0 0 0.5rem 0;">📝 {record['name']}</h3>
                        <p style="color: #64748B; margin: 0; font-size: 0.9rem;">
                            <strong>创建时间:</strong> {record['created_at']} | 
                            <strong>最后修改:</strong> {record['updated_at']}
                        </p>
                    </div>
                    <div style="display: flex; gap: 0.5rem;">
                        <span style="background: #FEF3C7; color: #D97706; padding: 0.25rem 0.75rem; border-radius: 20px; font-size: 0.8rem; font-weight: 600;">
                            暂存中
                        </span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # 操作按钮行
            col1, col2, col3, col4, col5 = st.columns(5)
            
            with col1:
                if st.button("👀 预览", key=f"preview_{record_id}", use_container_width=True):
                    st.session_state.preview_record_id = record_id
                    st.session_state.show_preview = True
                    st.rerun()
            
            with col2:
                if st.button("✏️ 编辑", key=f"edit_{record_id}", use_container_width=True):
                    st.session_state.edit_record_id = record_id
                    st.session_state.show_edit = True
                    st.rerun()
            
            with col3:
                if st.button("🚀 开始批改", key=f"grade_{record_id}", use_container_width=True, type="primary"):
                    # 这里可以跳转到批改页面
                    st.info(f"准备批改记录: {record['name']}")
            
            with col4:
                if st.button("📋 复制", key=f"copy_{record_id}", use_container_width=True):
                    # 复制记录
                    new_id = f"copy_{record_id}_{datetime.now().strftime('%H%M%S')}"
                    new_record = record.copy()
                    new_record['id'] = new_id
                    new_record['name'] = f"{record['name']}_副本"
                    new_record['created_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    st.session_state.draft_records[new_id] = new_record
                    save_draft_records_to_file()
                    st.success("记录已复制！")
                    st.rerun()
            
            with col5:
                if st.button("🗑️ 删除", key=f"delete_{record_id}", use_container_width=True, type="secondary"):
                    st.session_state.delete_record_id = record_id
                    st.session_state.show_delete_confirm = True
                    st.rerun()
    
    # 处理预览弹窗
    if st.session_state.get('show_preview', False):
        render_preview_modal()
    
    # 处理编辑弹窗
    if st.session_state.get('show_edit', False):
        render_edit_modal()
    
    # 处理删除确认弹窗
    if st.session_state.get('show_delete_confirm', False):
        render_delete_confirm_modal()

def render_preview_modal():
    """渲染预览弹窗"""
    record_id = st.session_state.get('preview_record_id')
    if not record_id or record_id not in st.session_state.draft_records:
        return
    
    record = st.session_state.draft_records[record_id]
    
    with st.expander("📄 记录预览", expanded=True):
        st.markdown(f"### 📝 {record['name']}")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**基本信息:**")
            st.json({
                "记录ID": record['id'],
                "创建时间": record['created_at'],
                "最后修改": record['updated_at'],
                "状态": record['status']
            })
        
        with col2:
            st.markdown("**数据概览:**")
            problem_data = record.get('problem_data', {})
            student_data = record.get('student_data', [])
            
            st.write(f"题目数量: {problem_data.get('题目数', 'N/A')}")
            st.write(f"总分: {problem_data.get('总分', 'N/A')}")
            st.write(f"学生数量: {len(student_data)}")
        
        if st.button("关闭预览", key="close_preview"):
            st.session_state.show_preview = False
            st.rerun()

def render_edit_modal():
    """渲染编辑弹窗"""
    record_id = st.session_state.get('edit_record_id')
    if not record_id or record_id not in st.session_state.draft_records:
        return
    
    record = st.session_state.draft_records[record_id]
    
    with st.expander("✏️ 编辑记录", expanded=True):
        st.markdown(f"### 编辑记录: {record['name']}")
        
        # 编辑记录名称
        new_name = st.text_input("记录名称", value=record['name'], key="edit_name")
        
        # 编辑手工调整
        st.markdown("**手工调整:**")
        manual_adjustments = record.get('manual_adjustments', {})
        
        # 简化的调整界面
        adjustment_text = st.text_area(
            "调整说明",
            value=manual_adjustments.get('notes', ''),
            height=100,
            key="edit_adjustments"
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("💾 保存修改", key="save_edit", type="primary"):
                st.session_state.draft_records[record_id]['name'] = new_name
                st.session_state.draft_records[record_id]['updated_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                st.session_state.draft_records[record_id]['manual_adjustments']['notes'] = adjustment_text
                save_draft_records_to_file()
                st.success("记录已保存！")
                st.session_state.show_edit = False
                st.rerun()
        
        with col2:
            if st.button("❌ 取消编辑", key="cancel_edit"):
                st.session_state.show_edit = False
                st.rerun()

def render_delete_confirm_modal():
    """渲染删除确认弹窗"""
    record_id = st.session_state.get('delete_record_id')
    if not record_id or record_id not in st.session_state.draft_records:
        return
    
    record = st.session_state.draft_records[record_id]
    
    st.error(f"⚠️ 确认删除记录: **{record['name']}**?")
    st.markdown("此操作不可撤销！")
    
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        if st.button("🗑️ 确认删除", key="confirm_delete", type="primary"):
            del st.session_state.draft_records[record_id]
            save_draft_records_to_file()
            st.success("记录已删除！")
            st.session_state.show_delete_confirm = False
            st.rerun()
    
    with col2:
        if st.button("❌ 取消", key="cancel_delete"):
            st.session_state.show_delete_confirm = False
            st.rerun()

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
        for job_id, task_info in st.session_state.jobs.items():
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
                    st.session_state.selected_job_id = job_id
                    st.switch_page("pages/score_report.py")
            
            with col2:
                if st.button("📈 可视化分析", key=f"viz_{job_id}", use_container_width=True):
                    st.session_state.selected_job_id = job_id
                    st.switch_page("pages/visualization.py")
            
            with col3:
                if st.button("📄 生成报告", key=f"report_{job_id}", use_container_width=True):
                    st.info(f"正在为任务 {record['task_name']} 生成报告...")
            
            with col4:
                if st.button("🗑️ 移除", key=f"remove_{job_id}", use_container_width=True, type="secondary"):
                    # 从jobs中移除
                    if "jobs" in st.session_state and job_id in st.session_state.jobs:
                        del st.session_state.jobs[job_id]
                    # 从completed_records中移除
                    if job_id in st.session_state.completed_records:
                        del st.session_state.completed_records[job_id]
                    st.success("记录已移除！")
                    st.rerun()

def render_statistics_overview():
    """渲染统计概览"""
    st.markdown("## 📊 统计概览")
    
    # 计算统计数据
    draft_count = len(st.session_state.draft_records)
    completed_count = len(st.session_state.get('completed_records', {}))
    
    # 从jobs中计算已完成的任务
    if "jobs" in st.session_state and st.session_state.jobs:
        for job_id, task_info in st.session_state.jobs.items():
            try:
                result = requests.get(f"{st.session_state.backend}/ai_grading/grade_result/{job_id}", timeout=5)
                result.raise_for_status()
                status = result.json().get("status", "未知")
                if status == "completed":
                    completed_count += 1
            except:
                continue
    
    total_records = draft_count + completed_count
    
    # 显示统计卡片
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div style="text-align: center; padding: 2rem; background: white; border-radius: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); border-top: 4px solid #1E3A8A;">
            <h1 style="color: #1E3A8A; margin: 0; font-size: 3rem;">{total_records}</h1>
            <p style="margin: 0.5rem 0 0 0; color: #64748B; font-weight: 600;">总记录数</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div style="text-align: center; padding: 2rem; background: white; border-radius: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); border-top: 4px solid #F59E0B;">
            <h1 style="color: #F59E0B; margin: 0; font-size: 3rem;">{draft_count}</h1>
            <p style="margin: 0.5rem 0 0 0; color: #64748B; font-weight: 600;">暂存记录</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div style="text-align: center; padding: 2rem; background: white; border-radius: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); border-top: 4px solid #10B981;">
            <h1 style="color: #10B981; margin: 0; font-size: 3rem;">{completed_count}</h1>
            <p style="margin: 0.5rem 0 0 0; color: #64748B; font-weight: 600;">已完成</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        completion_rate = (completed_count / total_records * 100) if total_records > 0 else 0
        st.markdown(f"""
        <div style="text-align: center; padding: 2rem; background: white; border-radius: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); border-top: 4px solid #8B5CF6;">
            <h1 style="color: #8B5CF6; margin: 0; font-size: 3rem;">{completion_rate:.1f}%</h1>
            <p style="margin: 0.5rem 0 0 0; color: #64748B; font-weight: 600;">完成率</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # 最近活动
    st.markdown("### 📅 最近活动")
    
    activities = []
    
    # 从暂存记录生成活动
    for record_id, record in st.session_state.draft_records.items():
        activities.append({
            "time": record['updated_at'],
            "action": "暂存记录",
            "details": f"保存了 '{record['name']}'",
            "type": "draft"
        })
    
    # 排序活动（最新的在前）
    activities.sort(key=lambda x: x['time'], reverse=True)
    
    # 显示最近5个活动
    for activity in activities[:5]:
        icon = "📝" if activity['type'] == "draft" else "✅"
        color = "#F59E0B" if activity['type'] == "draft" else "#10B981"
        
        st.markdown(f"""
        <div style="background: white; padding: 1rem; border-radius: 8px; margin: 0.5rem 0; box-shadow: 0 2px 4px rgba(0,0,0,0.1); border-left: 3px solid {color};">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <span style="font-size: 1.2rem; margin-right: 0.5rem;">{icon}</span>
                    <strong style="color: #1E3A8A;">{activity['action']}</strong>
                    <span style="color: #64748B; margin-left: 0.5rem;">- {activity['details']}</span>
                </div>
                <span style="color: #64748B; font-size: 0.85rem;">{activity['time']}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    if not activities:
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
